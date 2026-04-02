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
   - Notify the SensorEventBus (Observer pattern) so SSE clients
     receive the reading without polling.

3. Command drain task (asyncio):
   - Drain the asyncio command queue (filled by devices/router.py).
   - Publish each (adafruit_feed, state) directly to Adafruit IO.

Design pattern: Singleton
"""

import asyncio
import uuid
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from src.core.config import get_settings
from src.core.database import DatabaseManager
from src.core.mqtt import CommandQueue
from src.core.event_bus import SensorEventBus
from src.core.fire_alert import FireAlertObserver


class Gateway:
    """
    Singleton that owns the Adafruit IO MQTT connection and all
    background asyncio tasks.

    Usage
    -----
    await Gateway.get_instance().start()
    await Gateway.get_instance().stop()
    """

    _instance: "Gateway | None" = None

    def __init__(self) -> None:
        # None means "not yet received from Adafruit" for each feed.
        self._sensor_cache: dict = {
            "temperature": None,
            "humidity":    None,
            "illuminance": None,
        }
        # Tracks which feeds have sent a new value since the last DB save.
        # _cache_updated_at is only stamped once all three feeds have reported,
        # so the push loop never fires mid-batch (avoids duplicate documents).
        self._feeds_pending: set = set()
        self._cache_updated_at: datetime | None = None
        self._last_saved:       datetime | None = None
        self._client: mqtt.Client | None = None
        self._tasks: list[asyncio.Task] = []

    # ------------------------------------------------------------------ #
    # Singleton accessor                                                   #
    # ------------------------------------------------------------------ #

    @classmethod
    def get_instance(cls) -> "Gateway":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    # Feed helpers                                                         #
    # ------------------------------------------------------------------ #

    def _temp_feed(self)        -> str: return f"{get_settings().adafruit_io_username}/feeds/temperature"
    def _humidity_feed(self)    -> str: return f"{get_settings().adafruit_io_username}/feeds/humidity"
    def _illuminance_feed(self) -> str: return f"{get_settings().adafruit_io_username}/feeds/illuminance"

    # ------------------------------------------------------------------ #
    # Paho MQTT callbacks                                                  #
    # ------------------------------------------------------------------ #

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"🌐 Gateway connected to Adafruit IO ({get_settings().adafruit_mqtt_broker})")
            client.subscribe(self._temp_feed())
            client.subscribe(self._humidity_feed())
            client.subscribe(self._illuminance_feed())
            print("📡 Subscribed to temperature / humidity / illuminance feeds")
        else:
            print(f"❌ Adafruit IO connect failed. Code: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            print(
                f"⚠️  Adafruit IO disconnected (code={reason_code}). "
                "Paho auto-reconnect active — will retry in 2–30 s…"
            )

    def _on_message(self, client, userdata, msg):
        topic   = msg.topic
        payload = msg.payload.decode().strip()
        try:
            value = float(payload)
            if topic == self._temp_feed():
                self._sensor_cache["temperature"] = value
                self._feeds_pending.add("temperature")
            elif topic == self._humidity_feed():
                self._sensor_cache["humidity"] = value
                self._feeds_pending.add("humidity")
            elif topic == self._illuminance_feed():
                self._sensor_cache["illuminance"] = int(value)
                self._feeds_pending.add("illuminance")
            # Only mark the cache as ready to save once ALL three feeds
            # have delivered a new value — prevents saving a partial batch
            # and creating duplicate documents per Adafruit reading cycle.
            if self._feeds_pending >= {"temperature", "humidity", "illuminance"}:
                self._cache_updated_at = datetime.now(timezone.utc)
                self._feeds_pending.clear()
            print(
                f"📥 Adafruit [{topic.split('/')[-1]}] = {value}  "
                f"(T={self._sensor_cache['temperature']}  "
                f"H={self._sensor_cache['humidity']}  "
                f"Lux={self._sensor_cache['illuminance']})"
            )
        except ValueError:
            print(f"⚠️  Non-numeric payload on {topic}: {payload!r}")

    # ------------------------------------------------------------------ #
    # Asyncio tasks                                                        #
    # ------------------------------------------------------------------ #

    async def _sensor_push_loop(self) -> None:
        """
        Polls every second, but only persists a reading when:
          1. The root admin's is_collect flag is True.
          2. All three feeds have received at least one real value from Adafruit.
          3. The cache was updated (new MQTT message arrived) since the last save.
        This prevents writing fake 0/0/0 data and avoids duplicate rows.
        """
        db_manager = DatabaseManager.get_instance()
        event_bus  = SensorEventBus.get_instance()

        while True:
            await asyncio.sleep(1)
            try:
                # --- Guard 1: collection must be enabled ---
                admin_doc = await db_manager.database["users"].find_one(
                    {"username": "admin"}, {"is_collect": 1}
                )
                if not (admin_doc and admin_doc.get("is_collect")):
                    continue

                # --- Guard 2: all feeds must have real data ---
                if any(v is None for v in self._sensor_cache.values()):
                    continue

                # --- Guard 3: cache must be newer than last save ---
                if self._cache_updated_at is None:
                    continue
                if (
                    self._last_saved is not None
                    and self._cache_updated_at <= self._last_saved
                ):
                    continue

                now = datetime.now(timezone.utc)
                doc = {
                    "device_id":   "yolobit-living-room",
                    "temperature": self._sensor_cache["temperature"],
                    "humidity":    self._sensor_cache["humidity"],
                    "illuminance": self._sensor_cache["illuminance"],
                    "timestamp":   now,
                }
                await db_manager.database["sensor_readings"].insert_one(doc)
                self._last_saved = now
                # Notify all observers (SSE broadcaster, etc.)
                await event_bus.notify(doc)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"❌ Sensor push error: {exc}")

    async def _command_drain_loop(self) -> None:
        """Forward queued device commands to Adafruit IO."""
        queue = CommandQueue.get_instance().queue

        while True:
            try:
                adafruit_feed, state = await queue.get()
                full_feed = f"{get_settings().adafruit_io_username}/feeds/{adafruit_feed}"
                if self._client and self._client.is_connected():
                    self._client.publish(full_feed, state)
                    print(f"✅ Command published → Adafruit feed '{full_feed}' = {state}")
                else:
                    print(f"⚠️  Adafruit client not connected; command '{full_feed}={state}' dropped")
                queue.task_done()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"❌ Command drain error: {exc}")

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        """Connect to Adafruit IO and launch background asyncio tasks."""
        settings = get_settings()

        # Initialise the command queue (must happen inside the running event loop)
        CommandQueue.get_instance().init()

        # Build and connect the paho client.
        # Use a unique client_id per process run to avoid Adafruit IO's
        # "duplicate client" kick: if two sessions share the same id, the
        # broker immediately disconnects the older one, causing a reconnect
        # storm that burns through the free-tier 30-connections/min limit.
        client_id = f"smarthome-{uuid.uuid4().hex[:12]}"
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        self._client.username_pw_set(settings.adafruit_io_username, settings.adafruit_io_key)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message    = self._on_message
        # keepalive=30 stays under Render's ~55 s NAT idle timeout.
        # reconnect backoff: start at 5 s, cap at 120 s — avoids hammering
        # Adafruit IO (free tier: max 30 new connections per minute).
        self._client.reconnect_delay_set(min_delay=5, max_delay=120)
        self._client.connect_async(
            settings.adafruit_mqtt_broker,
            settings.adafruit_mqtt_port,
            keepalive=30,
        )
        self._client.loop_start()  # non-blocking paho thread
        print(f"🔌 MQTT client_id: {client_id}")

        # Launch asyncio background tasks
        self._tasks.append(asyncio.create_task(self._sensor_push_loop(),   name="sensor-push"))
        self._tasks.append(asyncio.create_task(self._command_drain_loop(), name="command-drain"))

        # Start the fire-alert observer (Observer pattern)
        FireAlertObserver.get_instance().start()

        print("🚀 Gateway started (embedded in FastAPI process)")

    async def stop(self) -> None:
        """Cancel background tasks and disconnect from Adafruit IO."""
        FireAlertObserver.get_instance().stop()

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

        print("🛑 Gateway stopped")


# ---------------------------------------------------------------------------
# Module-level helpers — preserve the old call-site API in main.py
# ---------------------------------------------------------------------------

async def start_gateway() -> None:
    await Gateway.get_instance().start()


async def stop_gateway() -> None:
    await Gateway.get_instance().stop()
