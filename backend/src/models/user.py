from enum import Enum
from datetime import datetime
from typing import Annotated
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict


# --- RBAC Roles ---------------------------------------------------------------

class Role(str, Enum):
    ADMIN = "admin"       # Full access: manage users, view all data, control all devices
    OPERATOR = "operator" # Control devices + view sensor data; cannot manage users
    VIEWER = "viewer"     # Read-only: view sensor data only


# --- ObjectId helper ----------------------------------------------------------

def validate_object_id(v: object) -> str:
    """Coerce a BSON ObjectId or string to a plain string."""
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str) and ObjectId.is_valid(v):
        return v
    raise ValueError(f"Invalid ObjectId: {v!r}")


PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]


# --- MongoDB document model ---------------------------------------------------

class UserDocument(BaseModel):
    """Represents a user document as stored in MongoDB."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: PyObjectId | None = Field(default=None, alias="_id")

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    hashed_password: str

    role: Role = Role.VIEWER
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_mongo(self) -> dict:
        """Serialise for insertion into MongoDB (exclude None _id so Mongo auto-generates it)."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        return data
