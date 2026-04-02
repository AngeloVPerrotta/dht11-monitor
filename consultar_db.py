import sqlite3

con = sqlite3.connect("sensor.db")

print("=== Últimas 10 lecturas ===")
for row in con.execute("SELECT * FROM lecturas ORDER BY id DESC LIMIT 10"):
    print(row)

print("\n=== Estadísticas ===")
cur = con.execute("SELECT COUNT(*), AVG(temp), AVG(hum), MIN(temp), MAX(temp) FROM lecturas")
count, avg_t, avg_h, min_t, max_t = cur.fetchone()
print(f"Total lecturas : {count}")
print(f"Temp promedio  : {avg_t:.1f}°C")
print(f"Hum promedio   : {avg_h:.1f}%")
print(f"Temp mín/máx   : {min_t}°C / {max_t}°C")

print("\n=== Últimas 10 alertas ===")
for row in con.execute("SELECT id, timestamp, tipo, valor, umbral FROM alertas ORDER BY id DESC LIMIT 10"):
    print(row)

print("\n=== Resumen de alertas ===")
cur = con.execute("SELECT COUNT(*) FROM alertas WHERE tipo = 'temperatura'")
alertas_temp = cur.fetchone()[0]
cur = con.execute("SELECT COUNT(*) FROM alertas WHERE tipo = 'humedad'")
alertas_hum = cur.fetchone()[0]
print(f"Alertas de temperatura : {alertas_temp}")
print(f"Alertas de humedad     : {alertas_hum}")

con.close()
