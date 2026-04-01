"""
src/core/gateway.py
===================
Runs the Adafruit IO MQTT client **inside** the FastAPI process.
No Mosquitto or external broker is needed.

Responsibilities
----------------
1. Adafruit MQTT client (runs in its own paho thread):
   - Subscribe to  {username}/feeds/temperature
                   {username}/feeds/humidity
                   {username}/feeds/illuminance
   - Cache the latest value for each sensor feed.

2. Sensor push task (asyncio, every 1 s):
   - Build a SensorReading snapshot from the cache.
   - Write it directly to MongoDB.

3. Command drain task (asyncio):
   - Drain the asyncio command queue (filled by devices/router.py).
   - Publish each (adafruit_feed, state) directly to Adafruit IO.
"""

import asyncio
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from src.core.config import settings
from src.core.database import get_database
from src.core.mqtt import init_command_queue, get_command_queue

# ---------------------------------------------------------------------------
# Sensor cache — written by the paho MQTT thread, read by asyncio tasks
# ---------------------------------------------------------------------------

_sensor_cache: dict = {
    "temperature": 0.0,
    "humidity": 0.0,
    "illuminance": 0,
}

# ---------------------------------------------------------------------------
# Adafruit IO MQTT client
# ---------------------------------------------------------------------------

_adafruit_client: mqtt.Client | None = None

# Feed paths
def _temp_feed()        -> str: return f"{settings.adafruit_io_username}/feeds/temperature"
def _humidity_feed()    -> str: return f"{settings.adafruit_io_username}/feeds/humidity"
def _illuminance_feed() -> str: return f"{settings.adafruit_io_username}/feeds/illuminance"


def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"🌐 Gateway connected to Adafruit IO ({settings.adafruit_mqtt_broker})")
        client.subscribe(_temp_feed())
        client.subscribe(_humidity_feed())
        client.subscribe(_illuminance_feed())
        print("📡 Subscribed to temperature / humidity / illuminance feeds")
    else:
        print(f"❌ Adafruit IO connect failed. Code: {reason_code}")


def _on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print(f"⚠️  Adafruit IO disconnected unexpectedly (code={reason_code}). Paho will retry…")


def _on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode().strip()
    try:
        value = float(payload)
        if topic == _temp_feed():
            _sensor_cache["temperature"] = value
        elif topic == _humidity_feed():
            _sensor_cache["humidity"] = value
        elif topic == _illuminance_feed():
            _sensor_cache["illuminance"] = int(value)
        print(
            f"📥 Adafruit [{topic.split('/')[-1]}] = {value}  "
            f"(T={_sensor_cache['temperature']}  "
            f"H={_sensor_cache['humidity']}  "
            f"Lux={_sensor_cache['illuminance']})"
        )
    except ValueError:
        print(f"⚠️  Non-numeric payload on {topic}: {payload!r}")


# ---------------------------------------------------------------------------
# Asyncio tasks
# ---------------------------------------------------------------------------

_tasks: list[asyncio.Task] = []


async def _sensor_push_loop() -> None:
    """Write a sensor snapshot to MongoDB every second."""
    while True:
        await asyncio.sleep(1)
        try:
            db = get_database()
            doc = {
                "device_id": "yolobit-living-room",
                "temperature": _sensor_cache["temperature"],
                "humidity": _sensor_cache["humidity"],
                "illuminance": _sensor_cache["illuminance"],
                "timestamp": datetime.now(timezone.utc),
            }
            await db["sensor_readings"].insert_one(doc)
            print(
                f"✅ Stored sensor: "
                f"T={doc['temperature']}°C  "
                f"H={doc['humidity']}%  "
                f"Lux={doc['illuminance']}"
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"❌ Sensor push error: {exc}")


async def _command_drain_loop() -> None:
    """Forward queued device commands to Adafruit IO."""
    queue = get_command_queue()
    while True:
        try:
            adafruit_feed, state = await queue.get()
            full_feed = f"{settings.adafruit_io_username}/feeds/{adafruit_feed}"
            if _adafruit_client and _adafruit_client.is_connected():
                _adafruit_client.publish(full_feed, state)
                print(f"✅ Command published → Adafruit feed '{full_feed}' = {state}")
            else:
                print(f"⚠️  Adafruit client not connected; command '{full_feed}={state}' dropped")
            queue.task_done()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"❌ Command drain error: {exc}")


# ---------------------------------------------------------------------------
# Public lifecycle API (called from main.py lifespan)
# ---------------------------------------------------------------------------

async def start_gateway() -> None:
    """Connect to Adafruit IO and launch background asyncio tasks."""
    global _adafruit_client

    # Initialise the command queue (must happen inside the running event loop)
    init_command_queue()

    # Build and connect the paho client
    _adafruit_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="smarthome-backend",
    )
    _adafruit_client.username_pw_set(
        settings.adafruit_io_username,
        settings.adafruit_io_key,
    )
    _adafruit_client.on_connect    = _on_connect
    _adafruit_client.on_disconnect = _on_disconnect
    _adafruit_client.on_message    = _on_message

    _adafruit_client.connect_async(
        settings.adafruit_mqtt_broker,
        settings.adafruit_mqtt_port,
        keepalive=60,
    )
    _adafruit_client.loop_start()   # non-blocking paho thread

    # Launch asyncio background tasks
    _tasks.append(asyncio.create_task(_sensor_push_loop(),   name="sensor-push"))
    _tasks.append(asyncio.create_task(_command_drain_loop(), name="command-drain"))

    print("🚀 Gateway started (embedded in FastAPI process)")


async def stop_gateway() -> None:
    """Cancel background tasks and disconnect from Adafruit IO."""
    for task in _tasks:
        task.cancel()
    await asyncio.gather(*_tasks, return_exceptions=True)
    _tasks.clear()

    if _adafruit_client:
        _adafruit_client.loop_stop()
        _adafruit_client.disconnect()

    print("🛑 Gateway stopped")
