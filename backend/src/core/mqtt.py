"""
Command queue bridge
====================
The devices router calls CommandQueue.get_instance().enqueue() which puts a
(feed, state) tuple into an asyncio.Queue.  Gateway drains that queue and
publishes directly to Adafruit IO — no local MQTT broker required.
"""

import asyncio
from typing import Tuple


class CommandQueue:
    """
    Singleton asyncio queue for device commands.

    Usage
    -----
    CommandQueue.get_instance().enqueue("light-livingroom", "ON")
    """

    _instance: "CommandQueue | None" = None

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Tuple[str, str]] | None = None

    # ------------------------------------------------------------------ #
    # Singleton accessor                                                   #
    # ------------------------------------------------------------------ #

    @classmethod
    def get_instance(cls) -> "CommandQueue":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def init(self) -> asyncio.Queue[Tuple[str, str]]:
        """Must be called inside the running asyncio event loop."""
        self._queue = asyncio.Queue()
        return self._queue

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    @property
    def queue(self) -> asyncio.Queue[Tuple[str, str]]:
        if self._queue is None:
            raise RuntimeError(
                "CommandQueue is not initialised. Call init() inside the event loop first."
            )
        return self._queue

    def enqueue(self, adafruit_feed: str, state: str) -> None:
        """Thread-safe: enqueue a command from sync or async context."""
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(self.queue.put_nowait, (adafruit_feed, state))
        print(f"📤 Queued command → feed={adafruit_feed!r}  state={state}")


# ---------------------------------------------------------------------------
# Module-level helpers — preserve the old call-site API
# ---------------------------------------------------------------------------

def init_command_queue() -> asyncio.Queue[Tuple[str, str]]:
    return CommandQueue.get_instance().init()


def get_command_queue() -> asyncio.Queue[Tuple[str, str]]:
    return CommandQueue.get_instance().queue


def enqueue_command(adafruit_feed: str, state: str) -> None:
    CommandQueue.get_instance().enqueue(adafruit_feed, state)
