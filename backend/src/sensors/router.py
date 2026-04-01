import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.auth.dependencies import get_current_active_user
from src.auth.schemas import UserPublic
from src.core.database import get_database

router = APIRouter(prefix="/sensors", tags=["Sensors"])


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
# Server-Sent Events — real-time stream pushed every second
# ---------------------------------------------------------------------------

@router.get(
    "/stream",
    summary="Real-time SSE stream of sensor readings (1 s interval)",
    response_class=StreamingResponse,
)
async def stream_sensors(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Opens a persistent Server-Sent Events connection.
    The backend pushes the latest sensor snapshot every second.
    Clients (browser / mobile) can consume this with the EventSource API.
    """
    async def event_generator():
        db = get_database()
        while True:
            try:
                doc = await db["sensor_readings"].find_one(sort=[("timestamp", -1)])
                if doc:
                    doc["_id"] = str(doc["_id"])
                    doc["timestamp"] = doc["timestamp"].isoformat()
                    yield f"data: {json.dumps(doc)}\n\n"
                else:
                    yield "data: {}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
