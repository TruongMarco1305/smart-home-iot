from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_active_user, require_roles
from src.auth.schemas import UserPublic
from src.core.database import get_database
from src.feeds.schemas import FeedCreate, FeedPublic
from src.models.user import Role

router = APIRouter(prefix="/feeds", tags=["Feeds"])


def _to_public(doc: dict) -> FeedPublic:
    return FeedPublic(
        id=str(doc["_id"]),
        key=doc["key"],
        label=doc["label"],
        created_at=doc.get("created_at", datetime.utcnow()),
    )


# ---------------------------------------------------------------------------
# List all feeds (any authenticated user — needed for the device dropdown)
# ---------------------------------------------------------------------------

@router.get("", response_model=list[FeedPublic], summary="List all Adafruit IO feeds")
async def list_feeds(
    _: UserPublic = Depends(get_current_active_user),
):
    db = get_database()
    docs = await db["feeds"].find().sort("key", 1).to_list(length=200)
    return [_to_public(d) for d in docs]


# ---------------------------------------------------------------------------
# Add a feed (admin only)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=FeedPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register an Adafruit IO feed key (admin only)",
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
async def create_feed(body: FeedCreate):
    db = get_database()

    existing = await db["feeds"].find_one({"key": body.key})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feed '{body.key}' already exists.",
        )

    doc = {
        "key": body.key,
        "label": body.label,
        "created_at": datetime.utcnow(),
    }
    result = await db["feeds"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_public(doc)


# ---------------------------------------------------------------------------
# Delete a feed (admin only)
# ---------------------------------------------------------------------------

@router.delete(
    "/{feed_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a registered feed (admin only)",
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
async def delete_feed(feed_id: str):
    if not ObjectId.is_valid(feed_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feed id")

    db = get_database()

    # Block deletion if any device is still using this feed
    feed = await db["feeds"].find_one({"_id": ObjectId(feed_id)})
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")

    in_use = await db["devices"].find_one({"adafruit_feed": feed["key"]})
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feed '{feed['key']}' is still used by device '{in_use['name']}'. Remove the device first.",
        )

    await db["feeds"].delete_one({"_id": ObjectId(feed_id)})
