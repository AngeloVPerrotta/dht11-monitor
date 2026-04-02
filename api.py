"""
DHT11 Sensor API — FastAPI
Corre con: uvicorn api:app --reload --port 8000
Documentación: http://localhost:8000/docs
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Configuración ──────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "sensor.db")

app = FastAPI(
    title="DHT11 Sensor API",
    description="API para consultar datos del sensor de temperatura y humedad DHT11.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Modelos Pydantic ───────────────────────────────────────────────────────────


class Alerta(BaseModel):
    id: int
    timestamp: str
    tipo: str
    valor: str
    umbral: str


class AlertaStats(BaseModel):
    total_alertas: int
    alertas_temp: int
    alertas_hum: int
    ultima_alerta: Optional[str]


class Lectura(BaseModel):
    id: int
    timestamp: str
    temp: float
    hum: float


class Stats(BaseModel):
    temp_promedio: float
    temp_min: float
    temp_max: float
    hum_promedio: float
    hum_min: float
    hum_max: float
    total_registros: int
    primer_registro: str
    ultimo_registro: str


# ── Base de datos ──────────────────────────────────────────────────────────────


@contextmanager
def get_db():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Base de datos no encontrada.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ── Endpoints ──────────────────────────────────────────────────────────────────


@app.get(
    "/data",
    response_model=Lectura,
    summary="Último registro",
    description="Devuelve el registro más reciente de la base de datos.",
)
def get_last():
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, timestamp, temp, hum FROM lecturas ORDER BY id DESC LIMIT 1"
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="No hay registros en la base de datos.")

    return dict(row)


@app.get(
    "/history",
    response_model=list[Lectura],
    summary="Historial de lecturas",
    description=(
        "Devuelve hasta `limit` registros ordenados de más antiguo a más nuevo. "
        "Filtrar desde una fecha/hora específica con el parámetro `desde`."
    ),
)
def get_history(
    limit: int = Query(default=50, ge=1, le=500, description="Cantidad de registros (1–500)."),
    desde: Optional[str] = Query(default=None, description="Timestamp mínimo, ej: '2024-01-15 10:00:00'."),
):
    with get_db() as conn:
        if desde is not None:
            rows = conn.execute(
                """
                SELECT id, timestamp, temp, hum
                FROM lecturas
                WHERE timestamp >= ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (desde, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, timestamp, temp, hum
                FROM (SELECT id, timestamp, temp, hum FROM lecturas ORDER BY id DESC LIMIT ?)
                ORDER BY id ASC
                """,
                (limit,),
            ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No se encontraron registros con los filtros indicados.")

    return [dict(r) for r in rows]


@app.get(
    "/stats",
    response_model=Stats,
    summary="Estadísticas globales",
    description="Calcula estadísticas agregadas sobre toda la base de datos.",
)
def get_stats():
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT
                ROUND(AVG(temp), 2)  AS temp_promedio,
                ROUND(MIN(temp), 2)  AS temp_min,
                ROUND(MAX(temp), 2)  AS temp_max,
                ROUND(AVG(hum),  2)  AS hum_promedio,
                ROUND(MIN(hum),  2)  AS hum_min,
                ROUND(MAX(hum),  2)  AS hum_max,
                COUNT(*)             AS total_registros,
                MIN(timestamp)       AS primer_registro,
                MAX(timestamp)       AS ultimo_registro
            FROM lecturas
            """
        ).fetchone()

    if row is None or row["total_registros"] == 0:
        raise HTTPException(status_code=404, detail="No hay registros en la base de datos.")

    return dict(row)


@app.get(
    "/alerts",
    response_model=list[Alerta],
    summary="Últimas alertas",
    description="Devuelve las últimas 20 alertas ordenadas de más reciente a más antigua.",
)
def get_alerts():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, tipo, valor, umbral FROM alertas ORDER BY id DESC LIMIT 20"
        ).fetchall()

    return [dict(r) for r in rows]


@app.get(
    "/alerts/stats",
    response_model=AlertaStats,
    summary="Estadísticas de alertas",
    description="Devuelve totales de alertas por tipo y timestamp de la última alerta.",
)
def get_alerts_stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM alertas").fetchone()[0]
        alertas_temp = conn.execute(
            "SELECT COUNT(*) FROM alertas WHERE tipo = 'temperatura'"
        ).fetchone()[0]
        alertas_hum = conn.execute(
            "SELECT COUNT(*) FROM alertas WHERE tipo = 'humedad'"
        ).fetchone()[0]
        ultima = conn.execute(
            "SELECT timestamp FROM alertas ORDER BY id DESC LIMIT 1"
        ).fetchone()

    return {
        "total_alertas": total,
        "alertas_temp": alertas_temp,
        "alertas_hum": alertas_hum,
        "ultima_alerta": ultima[0] if ultima else None,
    }


@app.get(
    "/predict",
    summary="Predicción de temperatura",
    description="Regresión lineal sobre los últimos 100 registros ordenados ASC. Predice los próximos 10 puntos (cada 2 s).",
)
def get_predict():
    try:
        import numpy as np
        from sklearn.linear_model import LinearRegression
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="numpy/scikit-learn no instalados. Ejecutar: python -m pip install numpy scikit-learn",
        )

    with get_db() as conn:
        rows = conn.execute(
            "SELECT temp, timestamp FROM lecturas ORDER BY id ASC LIMIT 100"
        ).fetchall()

    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="No hay suficientes datos para predecir.")

    temps = [float(r["temp"]) for r in rows]
    timestamps = [r["timestamp"] for r in rows]
    n = len(temps)

    X = np.array(range(n), dtype=float).reshape(-1, 1)
    y = np.array(temps, dtype=float)

    print(f"[predict] n={n}, X=[{X[0][0]:.0f}..{X[-1][0]:.0f}], "
          f"Y=[{min(temps):.2f}..{max(temps):.2f}], mean={y.mean():.2f}")

    model = LinearRegression()
    model.fit(X, y)

    print(f"[predict] coef={model.coef_[0]:.6f}, intercept={model.intercept_:.4f}")

    future_X = np.array(range(n, n + 10), dtype=float).reshape(-1, 1)
    pred_vals = model.predict(future_X)

    print(f"[predict] predicciones: {[round(float(v), 2) for v in pred_vals]}")

    from datetime import datetime, timedelta
    try:
        last_dt = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        last_dt = datetime.now()

    historico = [
        {"timestamp": timestamps[i], "temp": round(temps[i], 2)}
        for i in range(max(0, n - 20), n)
    ]

    prediccion = [
        {
            "timestamp": (last_dt + timedelta(milliseconds=2000 * (i + 1))).strftime("%Y-%m-%d %H:%M:%S"),
            "temp": round(float(pred_vals[i]), 2),
        }
        for i in range(10)
    ]

    return {"historico": historico, "prediccion": prediccion}


@app.get(
    "/anomalias",
    summary="Anomalías de temperatura",
    description="Valores a más de 2 desvíos estándar de la media (últimos 200 registros).",
)
def get_anomalias():
    try:
        import numpy as np
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="numpy no instalado. Ejecutar: python -m pip install numpy",
        )

    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, temp FROM lecturas ORDER BY id DESC LIMIT 200"
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No hay datos.")

    rows = list(reversed(rows))
    temps = [float(r["temp"]) for r in rows]
    media = float(np.mean(temps))
    desvio = float(np.std(temps))

    anomalias = []
    if desvio > 0:
        for r in rows:
            t = float(r["temp"])
            desviacion = abs(t - media) / desvio
            if desviacion > 2:
                anomalias.append({
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "temp": t,
                    "desviacion": round(desviacion, 2),
                })

    return {
        "anomalias": anomalias,
        "media": round(media, 2),
        "desvio": round(desvio, 2),
    }
