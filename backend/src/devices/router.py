from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_active_user, require_roles
from src.auth.schemas import UserPublic
from src.core.database import get_database
from src.devices.schemas import DeviceCommandBody, DeviceCreate, DevicePublic
from src.models.user import Role

router = APIRouter(prefix="/devices", tags=["Devices"])


def _to_public(doc: dict) -> DevicePublic:
    return DevicePublic(
        id=str(doc["_id"]),
        name=doc["name"],
        device_type=doc["device_type"],
        room=doc["room"],
        adafruit_feed=doc["adafruit_feed"],
        state=doc.get("state", "OFF"),
        is_online=doc.get("is_online", True),
        updated_at=doc.get("updated_at", datetime.utcnow()),
    )


# ---------------------------------------------------------------------------
# List all devices (any authenticated user)
# ---------------------------------------------------------------------------

@router.get("", response_model=list[DevicePublic], summary="List all registered devices")
async def list_devices(
    _: UserPublic = Depends(get_current_active_user),
):
    db = get_database()
    docs = await db["devices"].find().to_list(length=200)
    return [_to_public(d) for d in docs]


# ---------------------------------------------------------------------------
# Register a new device (admin only)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=DevicePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new device (admin only)",
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
async def create_device(body: DeviceCreate):
    db = get_database()

    # Prevent duplicates on adafruit_feed
    existing = await db["devices"].find_one({"adafruit_feed": body.adafruit_feed})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A device with adafruit_feed '{body.adafruit_feed}' already exists.",
        )

    now = datetime.utcnow()
    doc = {
        "name": body.name,
        "device_type": body.device_type,
        "room": body.room,
        "adafruit_feed": body.adafruit_feed,
        "state": "OFF",
        "is_online": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["devices"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_public(doc)


# ---------------------------------------------------------------------------
# Send a command to a device (operator or admin)
# ---------------------------------------------------------------------------

@router.patch(
    "/{device_id}/command",
    response_model=DevicePublic,
    summary="Turn a device ON or OFF (operator/admin)",
    dependencies=[Depends(require_roles(Role.ADMIN, Role.OPERATOR))],
)
async def command_device(device_id: str, body: DeviceCommandBody):
    """
    Updates the device state in MongoDB **and** publishes an MQTT command to
    the local broker so the gateway can forward it to Adafruit IO.
    """
    if not ObjectId.is_valid(device_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid device id")

    db = get_database()
    doc = await db["devices"].find_one({"_id": ObjectId(device_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    now = datetime.utcnow()
    await db["devices"].update_one(
        {"_id": ObjectId(device_id)},
        {"$set": {"state": body.state, "updated_at": now}},
    )
    doc["state"] = body.state
    doc["updated_at"] = now

    # Enqueue command → gateway.py will publish directly to Adafruit IO
    from src.core.mqtt import enqueue_command
    enqueue_command(
        adafruit_feed=doc["adafruit_feed"],
        state=body.state,
    )

    return _to_public(doc)
