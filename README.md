# 🏠 Smart Home IoT

A Python-based smart home system that connects physical sensors and actuators (via a **Yolo:Bit** microcontroller and **Adafruit IO**) to a cloud backend, enabling real-time monitoring and device control.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💡 **Light Control** | Turn lights on/off remotely |
| 💧 **Pump Control** | Turn water pump on/off remotely |
| 🌡️ **Temperature Monitoring** | Record and track room temperature |
| 💧 **Humidity Monitoring** | Record and track humidity levels |
| ☀️ **Illuminance Monitoring** | Record and track light intensity |

---

## 🏗️ Architecture

```
[Yolo:Bit Sensor]
       │  MQTT over TLS
       ▼
[Adafruit IO Cloud]
       │  MQTT Subscribe
       ▼
[Python IoT Gateway]  ──── HTTP POST (Bearer Token) ────▶  [FastAPI Backend]
                                                                    │
                                                               [Database]
```

**Data flow:**
1. The **Yolo:Bit** microcontroller reads sensor data (temperature, humidity, illuminance) and publishes it as JSON to an **Adafruit IO** feed via MQTT.
2. The **Python IoT Gateway** subscribes to the Adafruit IO feed, validates the payload using the shared Pydantic schema, and forwards it to the backend REST API.
3. The **FastAPI Backend** authenticates the gateway via a secret bearer token, stores the readings, and serves data to client apps.

---

## 📁 Project Structure

```
smart-home-iot/
├── backend/            # FastAPI REST API server
│   ├── main.py
│   ├── pyproject.toml
│   └── README.md
├── gateway/            # Python IoT gateway (MQTT → HTTP bridge)
│   ├── main.py
│   ├── pyproject.toml
│   └── README.md
├── shared_models/      # Shared Pydantic schemas used by both services
│   ├── __init__.py
│   └── schemas.py
├── .python-version     # Python 3.12
└── README.md
```

---

## 🛠️ Tech Stack

- **Python 3.12**
- **FastAPI** — REST API framework
- **Pydantic / pydantic-settings** — Data validation & settings management
- **Uvicorn** — ASGI server
- **paho-mqtt** — MQTT client for subscribing to Adafruit IO feeds
- **httpx** — Async HTTP client for gateway → backend communication
- **Adafruit IO** — Cloud MQTT broker for IoT device communication
- **Yolo:Bit** — Microcontroller that reads sensor data

---

## 🚀 Development Setup

### Prerequisites

- [**uv**](https://github.com/astral-sh/uv) (recommended Python package manager)
- Python 3.12+
- An [Adafruit IO](https://io.adafruit.com/) account

---

### 1. Clone the repository

```bash
git clone https://github.com/TruongMarco1305/smart-home-iot.git
cd smart-home-iot
```

---

### 2. Set up the Backend

```bash
cd backend
```

Create a `.env` file:

```env
GATEWAY_SECRET_TOKEN=your_super_secret_token
DEBUG_MODE=false
```

Install dependencies and run:

```bash
uv sync
uv run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

### 3. Set up the Gateway

```bash
cd gateway
```

Create a `.env` file:

```env
ADAFRUIT_IO_USERNAME=your_adafruit_username
ADAFRUIT_IO_KEY=your_adafruit_io_key
MQTT_BROKER=io.adafruit.com
MQTT_PORT=1883
BACKEND_URL=http://localhost:8000/api/data
GATEWAY_SECRET_TOKEN=your_super_secret_token
```

Install dependencies and run:

```bash
uv sync
uv run python main.py
```

---

### 4. Shared Models

The `shared_models/` package is a local dependency shared between the backend and gateway. It defines the core `SensorReading` schema:

```python
class SensorReading(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    illuminance: int
    timestamp: datetime
```

No installation is required — both services reference it directly via a relative `sys.path` import.

---

## 📡 API Reference

### `POST /api/data`

Receives a sensor reading from the IoT gateway.

**Headers:**
```
Authorization: Bearer <GATEWAY_SECRET_TOKEN>
```

**Request Body:**
```json
{
  "device_id": "yolobit-living-room",
  "temperature": 27.5,
  "humidity": 65.0,
  "illuminance": 420,
  "timestamp": "2026-03-13T10:00:00Z"
}
```

**Response:**
```json
{ "status": "success" }
```

---

## 🔒 Security

- The gateway authenticates to the backend using a **shared secret bearer token** defined in `.env` files.
- Never commit `.env` files to version control — they are included in `.gitignore`.
