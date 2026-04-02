from datetime import datetime
from pydantic import BaseModel, Field


class FeedCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100, description="Adafruit IO feed key, e.g. 'light-livingroom'")
    label: str = Field(..., min_length=1, max_length=100, description="Human-readable label, e.g. 'Living Room Light'")


class FeedPublic(BaseModel):
    id: str
    key: str
    label: str
    created_at: datetime
