"""
src/gateway/router.py
=====================
Admin-only endpoints to start / stop sensor data collection.

The collection flag lives on the root admin's user document as `is_collect`.
Only the admin account (username == "admin") has this field.

GET  /api/gateway/collection        → current is_collect value
POST /api/gateway/collection        → set is_collect (body: {"collecting": true/false})
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.auth.dependencies import require_roles
from src.auth.schemas import UserPublic
from src.core.database import get_database
from src.models.user import Role

router = APIRouter(prefix="/gateway", tags=["Gateway"])

_admin = Depends(require_roles(Role.ADMIN))

ROOT_ADMIN = "admin"  # username of the root account that owns is_collect


class CollectionStatus(BaseModel):
    collecting: bool


async def _get_admin_doc() -> dict:
    db = get_database()
    doc = await db["users"].find_one({"username": ROOT_ADMIN}, {"is_collect": 1})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Root admin account '{ROOT_ADMIN}' not found",
        )
    return doc


@router.get(
    "/collection",
    response_model=CollectionStatus,
    summary="Get current data-collection status (admin only)",
)
async def get_collection_status(_: UserPublic = _admin):
    doc = await _get_admin_doc()
    return CollectionStatus(collecting=bool(doc.get("is_collect", False)))


@router.post(
    "/collection",
    response_model=CollectionStatus,
    summary="Start or stop sensor data collection (admin only)",
)
async def set_collection_status(body: CollectionStatus, _: UserPublic = _admin):
    db = get_database()
    await db["users"].update_one(
        {"username": ROOT_ADMIN},
        {"$set": {"is_collect": body.collecting, "updated_at": datetime.now(timezone.utc)}},
    )
    return CollectionStatus(collecting=body.collecting)
