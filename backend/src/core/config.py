from functools import lru_cache
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

    # --- CORS ---
    # Comma-separated list of allowed origins.
    # e.g. "https://myapp.web.app,https://myapp.firebaseapp.com"
    # Localhost origins are always included so local dev works against any backend.
    cors_origins: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def get_cors_origins(self) -> list[str]:
        # Localhost origins are always allowed (needed for local dev hitting production).
        always_allowed = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "https://smart-iot-1234.web.app",
        ]
        if not self.cors_origins.strip():
            return always_allowed
        explicit = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # Merge without duplicates, preserving order
        return list(dict.fromkeys(explicit + always_allowed))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the application-wide Settings singleton."""
    return Settings()


# Convenience alias kept for backward compatibility during refactor
settings = get_settings()
