import serial
import csv
import os
import sqlite3
from datetime import datetime

# Configuración
PUERTO = "COM3"
BAUDRATE = 9600
ARCHIVO_CSV = "datos_sensor.csv"
ARCHIVO_DB = "sensor.db"

# ─── UMBRALES ────────────────────────────────────────────────
TEMP_MAX = 35.0
HUM_MIN  = 30.0

def verificar_alertas(temp, hum, timestamp):
    alertas = []

    if temp > TEMP_MAX:
        alertas.append({
            "tipo": "TEMPERATURA ALTA",
            "valor": f"{temp}°C",
            "umbral": f"> {TEMP_MAX}°C",
            "timestamp": timestamp
        })

    if hum < HUM_MIN:
        alertas.append({
            "tipo": "HUMEDAD BAJA",
            "valor": f"{hum}%",
            "umbral": f"< {HUM_MIN}%",
            "timestamp": timestamp
        })

    for alerta in alertas:
        print(f"\n⚠️  ALERTA: {alerta['tipo']}")
        print(f"   Valor:   {alerta['valor']}")
        print(f"   Umbral:  {alerta['umbral']}")
        print(f"   Hora:    {alerta['timestamp']}\n")

    return alertas

# ─── BASE DE DATOS ────────────────────────────────────────────
def iniciar_db():
    con = sqlite3.connect(ARCHIVO_DB)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lecturas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT    NOT NULL,
            temp      REAL    NOT NULL,
            hum       REAL    NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT    NOT NULL,
            tipo      TEXT    NOT NULL,
            valor     TEXT    NOT NULL,
            umbral    TEXT    NOT NULL
        )
    """)
    con.commit()
    return con

def insertar_db(con, timestamp, temp, hum):
    if not (0 <= temp <= 80):
        raise ValueError(f"Temperatura fuera de rango: {temp}")
    if not (0 <= hum <= 100):
        raise ValueError(f"Humedad fuera de rango: {hum}")
    con.execute(
        "INSERT INTO lecturas (timestamp, temp, hum) VALUES (?, ?, ?)",
        (timestamp, temp, hum)
    )
    con.commit()

def insertar_alerta_db(con, alerta):
    con.execute(
        "INSERT INTO alertas (timestamp, tipo, valor, umbral) VALUES (?, ?, ?, ?)",
        (alerta["timestamp"], alerta["tipo"], alerta["valor"], alerta["umbral"])
    )
    con.commit()

# ─── CSV ──────────────────────────────────────────────────────
def guardar_csv(timestamp, temp, hum):
    archivo_existe = os.path.isfile(ARCHIVO_CSV)
    with open(ARCHIVO_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "temp", "hum"])
        if not archivo_existe:
            writer.writeheader()
        writer.writerow({"timestamp": timestamp, "temp": temp, "hum": hum})

# ─── PARSEO ───────────────────────────────────────────────────
def parsear_linea(linea):
    try:
        partes = linea.strip().split(";")
        if len(partes) != 2:
            return None
        return float(partes[0]), float(partes[1])
    except ValueError:
        return None

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    con = iniciar_db()
    print(f"Base de datos lista: {ARCHIVO_DB}")
    print(f"Umbrales → Temp > {TEMP_MAX}°C | Hum < {HUM_MIN}%")
    print(f"Conectando a {PUERTO}...\n")

    try:
        with serial.Serial(PUERTO, BAUDRATE, timeout=2) as ser:
            print("Leyendo datos (Ctrl+C para detener)\n")
            while True:
                linea = ser.readline().decode("utf-8", errors="ignore")
                if not linea or linea.strip() == "ERROR":
                    continue

                resultado = parsear_linea(linea)
                if resultado is None:
                    continue

                temp, hum = resultado
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    insertar_db(con, timestamp, temp, hum)
                    guardar_csv(timestamp, temp, hum)
                    print(f"[{timestamp}] → temp: {temp}°C | hum: {hum}%  ✓")

                    # Verificar alertas
                    alertas = verificar_alertas(temp, hum, timestamp)
                    for alerta in alertas:
                        insertar_alerta_db(con, alerta)

                except ValueError as e:
                    print(f"[{timestamp}] ⚠ Dato descartado: {e}")

    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
    finally:
        con.close()
        print("Conexión a DB cerrada.")

if __name__ == "__main__":
    main()