from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_active_user, require_roles
from src.auth.schemas import UserPublic
from src.auth.utils import hash_password
from src.core.database import get_database
from src.models.user import Role
from src.users.schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def _to_public(doc: dict) -> UserPublic:
    return UserPublic(
        id=str(doc["_id"]),
        username=doc["username"],
        email=doc["email"],
        role=doc["role"],
        is_active=doc.get("is_active", True),
    )


# ---------------------------------------------------------------------------
# List all users (admin only)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[UserPublic],
    summary="List all users (admin only)",
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
async def list_users():
    db = get_database()
    docs = await db["users"].find().to_list(length=500)
    return [_to_public(d) for d in docs]


# ---------------------------------------------------------------------------
# Create a new user (admin only)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (admin only)",
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
async def create_user(body: UserCreate):
    db = get_database()

    if await db["users"].find_one({"username": body.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    if await db["users"].find_one({"email": body.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    now = datetime.utcnow()
    doc = {
        "username": body.username,
        "email": body.email,
        "hashed_password": hash_password(body.password),
        "role": body.role.value,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["users"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_public(doc)


# ---------------------------------------------------------------------------
# Get single user by id (admin, or the user themselves)
# ---------------------------------------------------------------------------

@router.get("/{user_id}", response_model=UserPublic, summary="Get a user by id")
async def get_user(
    user_id: str,
    current_user: UserPublic = Depends(get_current_active_user),
):
    if current_user.role != Role.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    db = get_database()
    doc = await db["users"].find_one({"_id": ObjectId(user_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_public(doc)


# ---------------------------------------------------------------------------
# Update user (admin for any field; users can only update their own password)
# ---------------------------------------------------------------------------

@router.patch("/{user_id}", response_model=UserPublic, summary="Update a user")
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: UserPublic = Depends(get_current_active_user),
):
    is_admin = current_user.role == Role.ADMIN
    is_self = current_user.id == user_id

    if not is_admin and not is_self:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    db = get_database()
    doc = await db["users"].find_one({"_id": ObjectId(user_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates: dict = {"updated_at": datetime.utcnow()}

    # Non-admins can only update their own password
    if body.password:
        updates["hashed_password"] = hash_password(body.password)

    if is_admin:
        if body.email is not None:
            updates["email"] = body.email
        if body.role is not None:
            updates["role"] = body.role.value
        if body.is_active is not None:
            updates["is_active"] = body.is_active

    await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    doc.update(updates)
    return _to_public(doc)
