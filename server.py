import sqlite3
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "sensor.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/datos")
def datos():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, timestamp, temp, hum FROM lecturas ORDER BY id DESC LIMIT 50"
        ).fetchall()
    finally:
        conn.close()

    data = [dict(row) for row in reversed(rows)]
    return jsonify(data)


@app.route("/api/stats")
def stats():
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT
                (SELECT temp FROM lecturas ORDER BY id DESC LIMIT 1) AS temp_actual,
                (SELECT hum  FROM lecturas ORDER BY id DESC LIMIT 1) AS hum_actual,
                ROUND(AVG(temp), 1) AS temp_promedio,
                ROUND(AVG(hum),  1) AS hum_promedio,
                ROUND(MAX(temp), 1) AS temp_max,
                ROUND(MIN(temp), 1) AS temp_min,
                COUNT(*) AS total_lecturas
            FROM lecturas
        """).fetchone()
    finally:
        conn.close()

    return jsonify(dict(row))


@app.route("/api/datos/hoy")
def datos_hoy():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, timestamp, temp, hum
            FROM lecturas
            WHERE timestamp >= datetime('now', '-24 hours')
            ORDER BY id ASC
            """
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
