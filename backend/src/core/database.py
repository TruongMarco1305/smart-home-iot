from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.core.config import get_settings


class DatabaseManager:
    """
    Singleton that owns the Motor async MongoDB client.

    Usage
    -----
    db = DatabaseManager.get_instance().database
    """

    _instance: "DatabaseManager | None" = None

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None

    # ------------------------------------------------------------------ #
    # Singleton accessor                                                   #
    # ------------------------------------------------------------------ #

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    async def connect(self) -> None:
        settings = get_settings()
        self._client = AsyncIOMotorClient(settings.mongodb_url)
        await self._client.admin.command("ping")

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    # ------------------------------------------------------------------ #
    # Database accessor                                                    #
    # ------------------------------------------------------------------ #

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._client is None:
            raise RuntimeError(
                "DatabaseManager is not connected. Call await connect() first."
            )
        return self._client[get_settings().mongodb_db_name]


# ---------------------------------------------------------------------------
# Module-level helpers — keep the old call-site API working unchanged
# ---------------------------------------------------------------------------

async def connect_db() -> None:
    await DatabaseManager.get_instance().connect()


async def close_db() -> None:
    await DatabaseManager.get_instance().close()


def get_database() -> AsyncIOMotorDatabase:
    return DatabaseManager.get_instance().database
