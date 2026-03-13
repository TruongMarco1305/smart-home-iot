from pydantic import BaseModel
from datetime import datetime

class SensorReading(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    illuminance: int
    timestamp: datetime