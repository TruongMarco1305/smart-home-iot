import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.auth.dependencies import get_current_active_user
from src.auth.schemas import UserPublic
from src.core.database import get_database
from src.core.event_bus import SensorEventBus
from src.core.alert_bus import AlertEventBus, AlertEvent

router = APIRouter(prefix="/sensors", tags=["Sensors"])


# ---------------------------------------------------------------------------
# DEV ONLY — manually fire a test alert (no real sensor data needed)
# ---------------------------------------------------------------------------

@router.post(
    "/alerts/test",
    summary="[DEV] Manually trigger a test alert",
    tags=["Dev"],
)
async def trigger_test_alert(
    level: Literal["fire", "high_temp", "high_light"] = Query(
        "fire", description="Alert level to simulate"
    ),
    temperature: float = Query(65.0),
    humidity: float = Query(40.0),
    illuminance: int = Query(4000),
    current_user: UserPublic = Depends(get_current_active_user),
):
    """
    Injects a synthetic AlertEvent directly into the AlertEventBus so you can
    verify the SSE stream and the frontend modal without waiting for real
    sensor thresholds to be crossed.
    """
    messages = {
        "fire":       "🔥 [TEST] Fire detected! High temperature and illuminance.",
        "high_temp":  "🌡️ [TEST] Temperature exceeds safe threshold.",
        "high_light": "☀️ [TEST] Unusually high illuminance detected.",
    }
    event = AlertEvent(
        level=level,
        message=messages[level],
        temperature=temperature,
        humidity=humidity,
        illuminance=illuminance,
        device_id="test-device",
    )
    await AlertEventBus.get_instance().notify(event)
    return {
        "ok": True,
        "triggered_by": current_user.username,
        "event": event.to_dict(),
    }


# ---------------------------------------------------------------------------
# Latest reading (most recent document in the collection)
# ---------------------------------------------------------------------------

@router.get("/latest", summary="Get the most recent sensor reading")
async def get_latest(_: UserPublic = Depends(get_current_active_user)):
    db = get_database()
    doc = await db["sensor_readings"].find_one(sort=[("timestamp", -1)])
    if doc is None:
        return {}
    doc["_id"] = str(doc["_id"])
    doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


# ---------------------------------------------------------------------------
# History with pagination
# ---------------------------------------------------------------------------

@router.get("/history", summary="Paginated sensor reading history")
async def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    device_id: str | None = Query(None),
    _: UserPublic = Depends(get_current_active_user),
):
    db = get_database()
    query: dict = {}
    if device_id:
        query["device_id"] = device_id

    skip = (page - 1) * limit
    cursor = db["sensor_readings"].find(query).sort("timestamp", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    total = await db["sensor_readings"].count_documents(query)

    results = []
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["timestamp"] = doc["timestamp"].isoformat()
        results.append(doc)

    return {"total": total, "page": page, "limit": limit, "data": results}


# ---------------------------------------------------------------------------
# Server-Sent Events — event-bus driven (Observer pattern)
# ---------------------------------------------------------------------------

@router.get(
    "/stream",
    summary="Real-time SSE stream of sensor readings (pushed on each new reading)",
    response_class=StreamingResponse,
)
async def stream_sensors(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Opens a persistent Server-Sent Events connection.

    Instead of polling MongoDB every second, this endpoint subscribes to the
    SensorEventBus.  The Gateway notifies the bus each time a new reading is
    stored, and the bus immediately pushes it to all connected SSE clients.

    Observer pattern
    ----------------
    Subject  : Gateway._sensor_push_loop  (calls event_bus.notify)
    Observer : the asyncio.Queue created here for this HTTP connection
    """
    # Each SSE connection gets its own asyncio.Queue and a unique name
    # so the event bus can route notifications independently.
    subscriber_id = f"sse-{current_user.username}-{uuid.uuid4().hex[:8]}"
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=10)
    bus = SensorEventBus.get_instance()

    async def _enqueue(reading: dict) -> None:
        # Drop the oldest item if the client is too slow, to avoid unbounded growth
        if queue.full():
            queue.get_nowait()
        await queue.put(reading)

    bus.subscribe(subscriber_id, _enqueue)

    async def event_generator():
        try:
            while True:
                try:
                    doc = await asyncio.wait_for(queue.get(), timeout=30)
                    # Serialise datetime objects
                    if isinstance(doc.get("timestamp"), datetime):
                        doc = {**doc, "timestamp": doc["timestamp"].isoformat()}
                    if "_id" in doc:
                        doc = {**doc, "_id": str(doc["_id"])}
                    yield f"data: {json.dumps(doc)}\n\n"
                except asyncio.TimeoutError:
                    # Send a keep-alive comment so the connection stays open
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe(subscriber_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Server-Sent Events — fire / environment alert stream (Observer pattern)
# ---------------------------------------------------------------------------

@router.get(
    "/alerts",
    summary="Real-time SSE stream of fire/environment alerts",
    response_class=StreamingResponse,
)
async def stream_alerts(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Opens a persistent SSE connection that delivers AlertEvents whenever the
    FireAlertObserver detects a dangerous environment condition.

    Observer pattern
    ----------------
    Subject  : FireAlertObserver (publishes to AlertEventBus)
    Observer : the asyncio.Queue created per SSE connection here
    """
    subscriber_id = f"alert-sse-{current_user.username}-{uuid.uuid4().hex[:8]}"
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=20)
    bus = AlertEventBus.get_instance()

    async def _enqueue(event_dict: dict) -> None:
        if queue.full():
            queue.get_nowait()
        await queue.put(event_dict)

    bus.subscribe(subscriber_id, _enqueue)

    async def event_generator():
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe(subscriber_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Latest reading (most recent document in the collection)
# ---------------------------------------------------------------------------

@router.get("/latest", summary="Get the most recent sensor reading")
async def get_latest(_: UserPublic = Depends(get_current_active_user)):
    db = get_database()
    doc = await db["sensor_readings"].find_one(sort=[("timestamp", -1)])
    if doc is None:
        return {}
    doc["_id"] = str(doc["_id"])
    doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


# ---------------------------------------------------------------------------
# History with pagination
# ---------------------------------------------------------------------------

@router.get("/history", summary="Paginated sensor reading history")
async def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    device_id: str | None = Query(None),
    _: UserPublic = Depends(get_current_active_user),
):
    db = get_database()
    query: dict = {}
    if device_id:
        query["device_id"] = device_id

    skip = (page - 1) * limit
    cursor = db["sensor_readings"].find(query).sort("timestamp", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    total = await db["sensor_readings"].count_documents(query)

    results = []
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["timestamp"] = doc["timestamp"].isoformat()
        results.append(doc)

    return {"total": total, "page": page, "limit": limit, "data": results}
