from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


# ---------- Request bodies ----------------------------------------------------

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    device_type: Literal["light", "pump"]
    room: str = Field(..., min_length=1, max_length=100)
    adafruit_feed: str = Field(
        ...,
        description="Adafruit IO feed key, e.g. 'light-livingroom'",
    )


class DeviceCommandBody(BaseModel):
    state: Literal["ON", "OFF"]


# ---------- Response body -----------------------------------------------------

class DevicePublic(BaseModel):
    id: str
    name: str
    device_type: str
    room: str
    adafruit_feed: str
    state: str
    is_online: bool
    updated_at: datetime
