"""
src/core/event_bus.py
=====================
Observer pattern implementation for sensor reading events.

How it works
------------
The Gateway (subject) calls SensorEventBus.get_instance().notify(reading)
every time a new sensor snapshot is stored to MongoDB.

Any component (observer) can subscribe with an async callback:

    async def my_handler(reading: dict) -> None:
        ...

    bus = SensorEventBus.get_instance()
    bus.subscribe("my-component", my_handler)
    # later:
    bus.unsubscribe("my-component")

Current observers
-----------------
- SSE stream endpoint (sensors/router.py): pushes each reading to connected
  browser clients in real time without polling MongoDB.

Potential future observers
--------------------------
- Anomaly detector: alert if temperature > threshold
- Data aggregator: compute rolling averages
- Notification service: push alerts to mobile / email
"""

import asyncio
from typing import Awaitable, Callable, Dict

# Type alias for an observer callback
SensorHandler = Callable[[dict], Awaitable[None]]


class SensorEventBus:
    """
    Singleton event bus that broadcasts new sensor readings to all
    registered async observers.

    Pattern: Observer (also known as Pub/Sub or Event Emitter)
    Subject: Gateway._sensor_push_loop  (calls notify)
    Observers: any component that calls subscribe()
    """

    _instance: "SensorEventBus | None" = None

    def __init__(self) -> None:
        self._observers: Dict[str, SensorHandler] = {}

    # ------------------------------------------------------------------ #
    # Singleton accessor                                                   #
    # ------------------------------------------------------------------ #

    @classmethod
    def get_instance(cls) -> "SensorEventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    # Observer management                                                  #
    # ------------------------------------------------------------------ #

    def subscribe(self, name: str, handler: SensorHandler) -> None:
        """Register an async observer under a unique name."""
        self._observers[name] = handler
        print(f"🔔 SensorEventBus: '{name}' subscribed ({len(self._observers)} total)")

    def unsubscribe(self, name: str) -> None:
        """Remove a previously registered observer."""
        self._observers.pop(name, None)
        print(f"🔕 SensorEventBus: '{name}' unsubscribed ({len(self._observers)} remaining)")

    # ------------------------------------------------------------------ #
    # Notification                                                         #
    # ------------------------------------------------------------------ #

    async def notify(self, reading: dict) -> None:
        """
        Called by the Gateway after each sensor snapshot is stored.
        Fires all registered observer callbacks concurrently.
        Any individual observer error is caught and logged so one
        bad handler cannot break the others.
        """
        if not self._observers:
            return

        results = await asyncio.gather(
            *[handler(reading) for handler in self._observers.values()],
            return_exceptions=True,
        )
        for name, result in zip(self._observers.keys(), results):
            if isinstance(result, Exception):
                print(f"❌ SensorEventBus: observer '{name}' raised {result!r}")
