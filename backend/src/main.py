# backend/src/main.py
from fastapi import FastAPI, HTTPException, Header
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared_models.schemas import SensorReading

# 1. Define your environment variables schema
class Settings(BaseSettings):
    gateway_secret_token: str
    debug_mode: bool = False
    
    # Tells Pydantic to read from the .env file in the current directory
    model_config = SettingsConfigDict(env_file=".env")

# 2. Instantiate the settings
settings = Settings()
server_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fastapi-backend")

app = FastAPI(title="Smart Home API")
fake_database = []

@app.on_event("startup")
def startup_event():
    server_mqtt.connect("localhost", 1883, 60)
    server_mqtt.loop_start()

@app.post("/api/data")
async def receive_sensor_data(
    reading: SensorReading, 
    # Require the secret token in the headers for security
    authorization: str = Header(None) 
):
    if authorization != settings.gateway_secret_token:
        raise HTTPException(status_code=401, detail="Unauthorized Gateway")

    fake_database.append(reading)
    print(f"✅ Received real data: Temp = {reading.temperature}°C")
    
    return {"status": "success"}

@app.post("/api/command")
async def send_device_command(command: DeviceCommand):
    mqtt_topic = f"commands/{command.device_type}/{command.room}"
    server_mqtt.publish(mqtt_topic, command.state)
    print(f"📤 Sent command: {command.device_type} in {command.room} -> {command.state}")
    return {
        "status": "success", 
        "message": "Command forwarded to local MQTT broker"
    }