from contextlib import asynccontextmanager
import sys
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.core.config import settings
from src.core.database import close_db, connect_db, get_database
from src.core.gateway import start_gateway, stop_gateway
from src.devices.router import router as devices_router
from src.gateway.router import router as gateway_router
from src.sensors.router import router as sensors_router
from src.users.router import router as users_router

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared_models.schemas import SensorReading

# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await connect_db()
    await _ensure_indexes()
    await _migrate_admin_is_collect()
    await start_gateway()
    yield
    # --- Shutdown ---
    await stop_gateway()
    await close_db()


async def _ensure_indexes():
    db = get_database()
    await db["users"].create_index("username", unique=True)
    await db["users"].create_index("email", unique=True)
    await db["devices"].create_index("adafruit_feed", unique=True)
    # TTL index: auto-delete sensor readings older than 7 days
    await db["sensor_readings"].create_index(
        "timestamp", expireAfterSeconds=7 * 24 * 3600
    )


async def _migrate_admin_is_collect():
    """Ensure the root admin document has the is_collect field (idempotent)."""
    db = get_database()
    await db["users"].update_one(
        {"username": "admin", "is_collect": {"$exists": False}},
        {"$set": {"is_collect": False}},
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Smart Home API",
    description=(
        "IoT Smart Home — login, real-time sensor monitoring via SSE, "
        "and light/pump device control."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router,    prefix="/api")
app.include_router(users_router,   prefix="/api")
app.include_router(devices_router, prefix="/api")
app.include_router(sensors_router, prefix="/api")
app.include_router(gateway_router, prefix="/api")


# ---------------------------------------------------------------------------
# Gateway ingestion endpoint
# ---------------------------------------------------------------------------

@app.post("/api/data", tags=["Gateway"], include_in_schema=False)
async def receive_sensor_data(
    reading: SensorReading,
    authorization: str = Header(None),
):
    """
    Called every second by the IoT gateway.
    Validates the shared secret, then persists the reading to MongoDB.
    """
    if authorization != f"Bearer {settings.gateway_secret_token}":
        raise HTTPException(status_code=401, detail="Unauthorized Gateway")

    db = get_database()
    await db["sensor_readings"].insert_one(reading.model_dump())
    return {"status": "success"}