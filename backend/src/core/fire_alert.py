"""
src/core/fire_alert.py
======================
Observer that watches every incoming SensorReading and raises an AlertEvent
when fire-like conditions are detected.

Thresholds
----------
- FIRE        : temperature >= 60 °C  AND  illuminance >= 3000 lux
- HIGH_TEMP   : temperature >= 50 °C  (without the lux spike)
- HIGH_LIGHT  : illuminance >= 5000 lux  (sudden flame / IR burst)

Cooldown: once an alert is fired, the same level is suppressed for
COOLDOWN_SECONDS to avoid flooding the frontend.

Design pattern: Observer
  Subject  →  SensorEventBus  (calls FireAlertObserver.handle)
  Observer →  FireAlertObserver  (evaluates thresholds, publishes AlertEvent)
  Subject  →  AlertEventBus  (FireAlertObserver calls notify)
"""

from datetime import datetime, timezone
from src.core.alert_bus import AlertEventBus, AlertEvent
from src.core.event_bus import SensorEventBus

# ---- Thresholds -------------------------------------------------------
FIRE_TEMP_THRESHOLD  = 60.0   # °C
FIRE_LUX_THRESHOLD   = 3000   # lux  (combined with temp → "fire")
HIGH_TEMP_THRESHOLD  = 50.0   # °C   (temp alone)
HIGH_LIGHT_THRESHOLD = 5000   # lux  (lux alone)

COOLDOWN_SECONDS = 30  # minimum seconds between alerts of the same level


class FireAlertObserver:
    """
    Singleton observer that detects fire/heat conditions and publishes
    AlertEvents to the AlertEventBus.
    """

    _instance: "FireAlertObserver | None" = None

    def __init__(self) -> None:
        # Maps alert level → last-fired UTC timestamp (float epoch)
        self._last_fired: dict[str, float] = {}

    @classmethod
    def get_instance(cls) -> "FireAlertObserver":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Register as an observer on the SensorEventBus."""
        SensorEventBus.get_instance().subscribe("fire-alert-observer", self.handle)
        print("🔥 FireAlertObserver: registered on SensorEventBus")

    def stop(self) -> None:
        SensorEventBus.get_instance().unsubscribe("fire-alert-observer")
        print("🔥 FireAlertObserver: unregistered")

    # ------------------------------------------------------------------ #
    # Core detection logic                                                 #
    # ------------------------------------------------------------------ #

    async def handle(self, reading: dict) -> None:
        temp  = float(reading.get("temperature", 0))
        lux   = int(reading.get("illuminance", 0))
        humid = float(reading.get("humidity", 0))
        dev   = reading.get("device_id", "unknown")

        alert: AlertEvent | None = None

        if temp >= FIRE_TEMP_THRESHOLD and lux >= FIRE_LUX_THRESHOLD:
            alert = AlertEvent(
                level="fire",
                message=(
                    f"🔥 FIRE DETECTED! Temperature {temp:.1f}°C and "
                    f"illuminance {lux} lux exceed critical thresholds."
                ),
                temperature=temp,
                humidity=humid,
                illuminance=lux,
                device_id=dev,
            )
        elif temp >= HIGH_TEMP_THRESHOLD:
            alert = AlertEvent(
                level="high_temp",
                message=f"⚠️ High temperature warning: {temp:.1f}°C",
                temperature=temp,
                humidity=humid,
                illuminance=lux,
                device_id=dev,
            )
        elif lux >= HIGH_LIGHT_THRESHOLD:
            alert = AlertEvent(
                level="high_light",
                message=f"⚠️ Unusual light intensity: {lux} lux",
                temperature=temp,
                humidity=humid,
                illuminance=lux,
                device_id=dev,
            )

        if alert and self._should_fire(alert.level):
            self._last_fired[alert.level] = datetime.now(timezone.utc).timestamp()
            print(f"🚨 Alert [{alert.level}]: {alert.message}")
            await AlertEventBus.get_instance().notify(alert)

    def _should_fire(self, level: str) -> bool:
        """Return True if the cooldown period for this level has elapsed."""
        last = self._last_fired.get(level, 0.0)
        now  = datetime.now(timezone.utc).timestamp()
        return (now - last) >= COOLDOWN_SECONDS
