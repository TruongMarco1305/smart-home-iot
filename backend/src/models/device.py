from typing import Annotated, Literal
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict

from src.models.user import validate_object_id

PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]

DeviceType = Literal["light", "pump"]
DeviceState = Literal["ON", "OFF"]


class DeviceDocument(BaseModel):
    """A controllable device registered in the system."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId | None = Field(default=None, alias="_id")

    name: str = Field(..., min_length=1, max_length=100,
                      description="Human-readable name, e.g. 'Living Room Light'")
    device_type: DeviceType
    room: str = Field(..., min_length=1, max_length=100)

    # Mirrors the Adafruit IO feed name used for this device
    # e.g. "light-livingroom"  →  {username}/feeds/light-livingroom
    adafruit_feed: str = Field(..., description="Adafruit IO feed key for this device")

    state: DeviceState = "OFF"
    is_online: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)
