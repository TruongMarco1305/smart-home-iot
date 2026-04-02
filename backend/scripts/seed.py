"""
Seed script — run once to create a default admin user.

Usage (from the backend/ directory):
    uv run python scripts/seed.py
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.core.database import close_db, connect_db, get_database
from src.auth.utils import hash_password

DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@smarthome.local",
    "password": "admin1234",   # ← change after first login
}


async def seed():
    print("🌱  Connecting to MongoDB…")
    await connect_db()
    db = get_database()

    existing = await db["users"].find_one({"username": DEFAULT_ADMIN["username"]})
    if existing:
        print(f"⚠️   User '{DEFAULT_ADMIN['username']}' already exists — skipping.")
    else:
        now = datetime.now(timezone.utc)
        doc = {
            "username": DEFAULT_ADMIN["username"],
            "email": DEFAULT_ADMIN["email"],
            "hashed_password": hash_password(DEFAULT_ADMIN["password"]),
            "role": "admin",
            "is_active": True,
            "is_collect": False,
            "created_at": now,
            "updated_at": now,
        }
        result = await db["users"].insert_one(doc)
        print(f"✅  Admin user created  (id={result.inserted_id})")
        print(f"    username : {DEFAULT_ADMIN['username']}")
        print(f"    password : {DEFAULT_ADMIN['password']}  ← please change this!")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
