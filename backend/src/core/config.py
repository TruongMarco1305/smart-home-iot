from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Gateway ---
    gateway_secret_token: str
    debug_mode: bool = False

    # --- MongoDB ---
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "smart_home"

    # --- JWT ---
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Adafruit IO (MQTT broker for sensor data + device commands) ---
    adafruit_io_username: str
    adafruit_io_key: str
    adafruit_mqtt_broker: str = "io.adafruit.com"
    adafruit_mqtt_port: int = 1883

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
