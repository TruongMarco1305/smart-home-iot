"""
src/core/alert_bus.py
=====================
Singleton event bus that broadcasts alert events to all registered observers.

This is a second-level bus sitting above SensorEventBus:

    SensorEventBus  →  FireAlertObserver  →  AlertEventBus  →  SSE clients

Pattern: Observer (same as SensorEventBus, but for alert payloads)
"""

import asyncio
from typing import Awaitable, Callable, Dict, Literal
from dataclasses import dataclass, field
from datetime import datetime, timezone

AlertHandler = Callable[[dict], Awaitable[None]]


@dataclass
class AlertEvent:
    """Payload broadcast to every alert observer."""
    level:       Literal["fire", "high_temp", "high_light"]
    message:     str
    temperature: float
    humidity:    float
    illuminance: int
    device_id:   str
    timestamp:   datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "level":       self.level,
            "message":     self.message,
            "temperature": self.temperature,
            "humidity":    self.humidity,
            "illuminance": self.illuminance,
            "device_id":   self.device_id,
            "timestamp":   self.timestamp.isoformat(),
        }


class AlertEventBus:
    """
    Singleton event bus for alert events.

    Usage
    -----
    AlertEventBus.get_instance().subscribe("my-handler", my_async_fn)
    await AlertEventBus.get_instance().notify(alert_event)
    """

    _instance: "AlertEventBus | None" = None

    def __init__(self) -> None:
        self._observers: Dict[str, AlertHandler] = {}

    @classmethod
    def get_instance(cls) -> "AlertEventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, name: str, handler: AlertHandler) -> None:
        self._observers[name] = handler
        print(f"🔔 AlertEventBus: '{name}' subscribed ({len(self._observers)} total)")

    def unsubscribe(self, name: str) -> None:
        self._observers.pop(name, None)
        print(f"🔕 AlertEventBus: '{name}' unsubscribed ({len(self._observers)} remaining)")

    async def notify(self, event: AlertEvent) -> None:
        if not self._observers:
            return
        payload = event.to_dict()
        results = await asyncio.gather(
            *[handler(payload) for handler in self._observers.values()],
            return_exceptions=True,
        )
        for name, result in zip(self._observers.keys(), results):
            if isinstance(result, Exception):
                print(f"❌ AlertEventBus: observer '{name}' raised {result!r}")
