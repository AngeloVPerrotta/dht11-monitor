# DHT11 Environmental Monitor

A full-stack IoT project that reads temperature and humidity data from a DHT11 sensor connected to an Arduino, stores it in a local SQLite database, and exposes it through two REST APIs and a real-time web dashboard with machine learning features.

---

## Circuit

![Circuit placeholder](https://placehold.co/800x400?text=Arduino+%2B+DHT11+Circuit)

> **Wiring:** DHT11 DATA → Arduino digital pin 2 · VCC → 5V · GND → GND  
> Serial output format over USB: `temperature;humidity` at 9600 baud.

---

## Features

- **Real-time monitoring** — temperature and humidity updated every 5 seconds in the browser
- **ML prediction** — linear regression (scikit-learn) over the last 100 readings to forecast the next 10 data points
- **Anomaly detection** — flags readings more than 2 standard deviations from the historical mean
- **REST API** — two independent servers (Flask + FastAPI) exposing structured JSON endpoints
- **Interactive dashboard** — glassmorphism UI with Chart.js charts, sticky metrics, alerts table, and system status panel

---

## Tech Stack

| Layer | Technology |
|---|---|
| Sensor | Arduino Uno + DHT11 |
| Data ingestion | Python `pyserial` |
| Storage | SQLite |
| Data export | CSV |
| API (lightweight) | Flask 3 |
| API (full-featured) | FastAPI + Uvicorn |
| ML | scikit-learn, NumPy |
| Frontend | HTML/CSS/JS, Chart.js 4 |

---

## Project Structure

```
proyecto sensor/
├── sensor.py          # Reads serial data from Arduino → DB + CSV
├── server.py          # Flask API  (port 5000)
├── api.py             # FastAPI    (port 8000)
├── dashboard.html     # Frontend dashboard
├── consultar_db.py    # CLI utility to inspect the database
├── sensor.db          # SQLite database (git-ignored)
└── datos_sensor.csv   # CSV backup (git-ignored)
```

---

## Installation

### Prerequisites

- Python 3.10+
- Arduino IDE (to flash the sensor sketch)
- A DHT11 sensor wired to the Arduino

### 1 — Clone the repository

```bash
git clone <your-repo-url>
cd "proyecto sensor"
```

### 2 — Install Python dependencies

```bash
pip install flask flask-cors fastapi uvicorn pyserial numpy scikit-learn
```

### 3 — Flash the Arduino

Upload the following sketch to your Arduino board. It reads the DHT11 and sends data over Serial in `temp;hum` format every 2 seconds:

```cpp
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (!isnan(h) && !isnan(t)) {
    Serial.print(t);
    Serial.print(";");
    Serial.println(h);
  } else {
    Serial.println("ERROR");
  }
  delay(2000);
}
```

### 4 — Configure the serial port

Open `sensor.py` and set the correct COM port:

```python
PUERTO = "COM3"   # Windows: COM3, COM4, etc.
                  # Linux/Mac: /dev/ttyUSB0 or /dev/tty.usbmodem*
```

---

## Running the Project

All four components can run simultaneously in separate terminals.

### Terminal 1 — Data ingestion (sensor → DB)

```bash
python sensor.py
```

Connects to the Arduino over serial, reads `temp;hum` lines, writes each reading to `lecturas` in `sensor.db`, saves a CSV backup, and triggers alert checks.

### Terminal 2 — Flask API (port 5000)

```bash
python server.py
```

Lightweight server that feeds the dashboard with historical and real-time data.

### Terminal 3 — FastAPI (port 8000)

```bash
uvicorn api:app --reload --port 8000
```

Full-featured API with ML endpoints. Interactive docs available at `http://localhost:8000/docs`.

### Terminal 4 — Dashboard

Open `dashboard.html` directly in a browser (no build step required):

```
file:///path/to/proyecto sensor/dashboard.html
```

Or serve it with any static server:

```bash
python -m http.server 3000
# then open http://localhost:3000/dashboard.html
```

### Inspect the database (optional)

```bash
python consultar_db.py
```

Prints the last 10 sensor readings, global statistics, the last 10 alerts, and an alert summary to the terminal.

---

## API Reference

### Flask — `http://localhost:5000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/datos` | Last 50 readings ordered oldest → newest |
| GET | `/api/datos/hoy` | All readings from the last 24 hours |
| GET | `/api/stats` | Current temp/humidity + aggregated statistics |

#### Example — `/api/stats`

```json
{
  "temp_actual": 26.5,
  "hum_actual": 58.0,
  "temp_promedio": 25.8,
  "temp_max": 31.2,
  "temp_min": 22.1,
  "total_lecturas": 4320
}
```

---

### FastAPI — `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/data` | Single most recent reading |
| GET | `/history` | Paginated history — params: `limit` (1–500), `desde` (timestamp) |
| GET | `/stats` | Aggregated stats with min/max/avg for temp and humidity |
| GET | `/alerts` | Last 20 alerts, newest first |
| GET | `/alerts/stats` | Alert counts by type and timestamp of last alert |
| GET | `/predict` | Linear regression prediction for next 10 readings |
| GET | `/anomalias` | Readings more than 2σ from the historical mean |

#### Example — `/predict`

```json
{
  "historico": [
    { "timestamp": "2024-01-15 14:30:00", "temp": 25.3 }
  ],
  "prediccion": [
    { "timestamp": "2024-01-15 14:30:02", "temp": 25.4 }
  ]
}
```

#### Example — `/anomalias`

```json
{
  "anomalias": [
    { "id": 312, "timestamp": "2024-01-15 13:02:44", "temp": 31.8, "desviacion": 2.34 }
  ],
  "media": 25.2,
  "desvio": 2.8
}
```

---

## Alert Thresholds

Configured in `sensor.py`. Defaults:

| Condition | Threshold |
|---|---|
| High temperature | > 35 °C |
| Low humidity | < 30 % |

Change `TEMP_MAX` and `HUM_MIN` at the top of `sensor.py` to adjust.

---

## License

MIT
