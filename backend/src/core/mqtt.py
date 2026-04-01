"""
Command queue bridge
====================
The devices router calls enqueue_command() which puts a (feed, state) tuple
into an asyncio.Queue.  gateway.py drains that queue and publishes directly
to Adafruit IO — no local MQTT broker (Mosquitto) required.
"""

import asyncio
from typing import Tuple

# Queue items: (adafruit_feed_key, state)  e.g. ("light-livingroom", "ON")
_command_queue: asyncio.Queue[Tuple[str, str]] | None = None


def init_command_queue() -> asyncio.Queue[Tuple[str, str]]:
    global _command_queue
    _command_queue = asyncio.Queue()
    return _command_queue


def get_command_queue() -> asyncio.Queue[Tuple[str, str]]:
    if _command_queue is None:
        raise RuntimeError("Command queue not initialised — call init_command_queue() first")
    return _command_queue


def enqueue_command(adafruit_feed: str, state: str) -> None:
    """Thread-safe: put a command onto the queue from sync or async code."""
    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(get_command_queue().put_nowait, (adafruit_feed, state))
    print(f"📤 Queued command → feed={adafruit_feed!r}  state={state}")
