"""
src/gateway/router.py
=====================
Admin-only endpoints to start / stop sensor data collection.

POST /api/gateway/collection        → start or stop (body: {"collecting": true/false})
GET  /api/gateway/collection        → current status
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.auth.dependencies import require_roles
from src.auth.schemas import UserPublic
from src.core.gateway import Gateway
from src.models.user import Role

router = APIRouter(prefix="/gateway", tags=["Gateway"])

_admin = Depends(require_roles(Role.ADMIN))


class CollectionStatus(BaseModel):
    collecting: bool


@router.get(
    "/collection",
    response_model=CollectionStatus,
    summary="Get current data-collection status",
    dependencies=[_admin],
)
async def get_collection_status(_: UserPublic = _admin):
    return CollectionStatus(collecting=Gateway.get_instance().collecting)


@router.post(
    "/collection",
    response_model=CollectionStatus,
    summary="Start or stop sensor data collection (admin only)",
    dependencies=[_admin],
)
async def set_collection_status(
    body: CollectionStatus,
    _: UserPublic = _admin,
):
    gw = Gateway.get_instance()
    if body.collecting:
        gw.start_collection()
    else:
        gw.stop_collection()
    return CollectionStatus(collecting=gw.collecting)
