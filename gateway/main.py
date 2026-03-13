# gateway/src/main.py
import os
import json
import httpx
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from datetime import datetime, timezone
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared_models.schemas import SensorReading

# 1. Load environment variables from the .env file
load_dotenv()

ADAFRUIT_USERNAME = os.getenv("ADAFRUIT_IO_USERNAME")
ADAFRUIT_KEY = os.getenv("ADAFRUIT_IO_KEY")
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
BACKEND_URL = os.getenv("BACKEND_URL")

# Let's assume your Yolo:Bit publishes a JSON string to a feed called 'sensor-data'
# The feed path format in Adafruit IO is always: username/feeds/feed-name
SENSOR_FEED = f"{ADAFRUIT_USERNAME}/feeds/sensor-data"

# 2. Define MQTT Callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"🌐 Connected to MQTT Broker: {MQTT_BROKER}")
        # Subscribe to the specific feed
        client.subscribe(SENSOR_FEED)
        print(f"📡 Subscribed to feed: {SENSOR_FEED}")
    else:
        print(f"❌ Failed to connect. Code: {reason_code}")

def on_message(client, userdata, msg):
    """Triggered every time the Yolo:Bit sends data to Adafruit IO."""
    print(f"📥 Message received on {msg.topic}")
    
    try:
        # Assuming Yolo:Bit sends: {"temperature": 25, "humidity": 60, "illuminance": 300}
        payload = json.loads(msg.payload.decode())
        
        # 3. Construct the shared Pydantic model
        reading = SensorReading(
            device_id="yolobit-living-room",
            temperature=payload.get("temperature", 0.0),
            humidity=payload.get("humidity", 0.0),
            illuminance=payload.get("illuminance", 0),
            timestamp=datetime.now(timezone.utc)
        )
        
        # 4. Forward to the FastAPI backend using the secret token
        # Note: In production, load the token from the gateway's .env file too!
        headers = {"Authorization": "Bearer my_super_secret_team_token"}
        
        response = httpx.post(
            BACKEND_URL, 
            json=reading.model_dump(mode='json'),
            headers=headers
        )
        response.raise_for_status()
        print("✅ Data successfully forwarded to Backend.")
        
    except json.JSONDecodeError:
        print(f"⚠️ Could not decode JSON payload: {msg.payload}")
    except httpx.HTTPError as e:
        print(f"❌ Failed to send to backend: {e}")
    except Exception as e:
        print(f"❌ Error processing message: {e}")

def main():
    print("🚀 Starting IoT Gateway...")
    
    # 5. Initialize the MQTT Client (Using the required V2 API format)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="python-gateway")
    
    # Set Adafruit IO credentials
    client.username_pw_set(ADAFRUIT_USERNAME, ADAFRUIT_KEY)
    
    # Attach callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect and start the loop
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # loop_forever() handles reconnects and blocks the thread to keep listening
    client.loop_forever()

if __name__ == "__main__":
    main()