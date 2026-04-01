from datetime import datetime
from typing import Annotated
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict

from src.models.user import validate_object_id

PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]


class SensorReadingDocument(BaseModel):
    """One sensor snapshot stored in MongoDB."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId | None = Field(default=None, alias="_id")

    device_id: str          # e.g. "yolobit-living-room"
    temperature: float
    humidity: float
    illuminance: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)
