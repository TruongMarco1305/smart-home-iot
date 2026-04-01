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
       │  MQTT (Adafruit IO feeds)
       ▼
[Adafruit IO Cloud] ◄──── device commands (ON/OFF) published back
       │  MQTT Subscribe (temperature / humidity / illuminance)
       ▼
┌──────────────────────────────────────────────┐
│           FastAPI Backend                    │
│  ┌────────────────────────────────────────┐  │
│  │  Embedded Gateway (src/core/gateway.py)│  │
│  │  • paho MQTT client → Adafruit IO      │  │
│  │  • sensor push loop (every 1 s → DB)   │  │
│  │  • command drain loop (queue → MQTT)   │  │
│  └────────────────────────────────────────┘  │
│  REST API  •  SSE stream  •  Auth / RBAC     │
└──────────────────┬───────────────────────────┘
                   │
              [MongoDB]
```

**No external MQTT broker (Mosquitto) required.**

**Data flow:**
1. The **Yolo:Bit** publishes sensor values to individual **Adafruit IO** MQTT feeds.
2. The **embedded gateway** (`src/core/gateway.py`) subscribes to those feeds inside the FastAPI process, caches the latest values, and writes a snapshot to MongoDB every second.
3. When a user sends a device command via the REST API, it is placed in an in-process `asyncio.Queue`. The command drain loop picks it up and publishes it directly to the correct Adafruit IO feed, which the Yolo:Bit receives.
4. The frontend consumes live sensor data via an **SSE stream** (`GET /api/sensors/stream`).

---

## 📁 Project Structure

```
smart-home-iot/
├── backend/                  # FastAPI backend (gateway embedded inside)
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py     # All settings (pydantic-settings)
│   │   │   ├── database.py   # Async Motor MongoDB client
│   │   │   ├── gateway.py    # Embedded Adafruit IO MQTT client + tasks
│   │   │   └── mqtt.py       # asyncio command queue bridge
│   │   ├── auth/             # Login, JWT, RBAC dependencies
│   │   ├── devices/          # Device CRUD + ON/OFF command endpoint
│   │   ├── sensors/          # Latest reading, history, SSE stream
│   │   ├── users/            # User management (admin)
│   │   └── models/           # MongoDB document models
│   ├── scripts/seed.py       # Creates default admin user
│   ├── pyproject.toml
│   └── .env
├── gateway/                  # Standalone gateway (kept for reference / edge deploy)
├── shared_models/            # Shared Pydantic schemas (SensorReading, DeviceCommand)
└── docs/API.md               # Frontend integration guide
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
- MongoDB (local or Atlas)

> **No Mosquitto or any other MQTT broker is needed** — the backend connects directly to Adafruit IO.

---

### 1. Clone the repository

```bash
git clone https://github.com/TruongMarco1305/smart-home-iot.git
cd smart-home-iot
```

---

### 2. Configure the backend

```bash
cd backend
cp .env.example .env
```

Edit `.env`:

```env
GATEWAY_SECRET_TOKEN=your_super_secret_token
DEBUG_MODE=True

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=smart_home

# JWT — generate with: openssl rand -hex 32
JWT_SECRET_KEY=your_random_secret

# Adafruit IO
ADAFRUIT_IO_USERNAME=your_adafruit_username
ADAFRUIT_IO_KEY=your_adafruit_io_key
ADAFRUIT_MQTT_BROKER=io.adafruit.com
ADAFRUIT_MQTT_PORT=1883
```

---

### 3. Install dependencies, seed the DB, and run

```bash
uv sync
uv run python scripts/seed.py   # creates admin / admin1234
uv run uvicorn src.main:app --reload
```

The API is available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

On startup the backend automatically connects to Adafruit IO and begins receiving sensor data. No separate gateway process is required.

---

### 4. Shared Models

`shared_models/` contains Pydantic schemas shared across the project:

```python
class SensorReading(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    illuminance: int
    timestamp: datetime

class DeviceCommand(BaseModel):
    device_id: str
    device_type: Literal["light", "pump"]
    room: str
    state: Literal["ON", "OFF"]
```

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
