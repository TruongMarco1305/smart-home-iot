from pydantic import BaseModel
from datetime import datetime

class SensorReading(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    illuminance: int
    timestamp: datetime

class DeviceCommand(BaseModel):
    device_type: Literal["light", "pump"]
    room: str
    state: Literal["ON", "OFF"]