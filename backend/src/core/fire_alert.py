"""
src/core/fire_alert.py
======================
Previously contained threshold-based fire detection logic.

Fire alerts are now triggered directly by the Adafruit IO `fire-alert` MQTT
feed.  When the Yolo:Bit publishes any value to that feed, the gateway's
`_on_message` handler calls `_handle_fire_alert`, which pushes an AlertEvent
straight to the AlertEventBus — no threshold evaluation needed.

This file is kept as a compatibility shim so any external imports still resolve.
"""

from src.core.alert_bus import AlertEventBus, AlertEvent  # re-export for convenience

__all__ = ["AlertEventBus", "AlertEvent"]
