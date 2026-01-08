import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://admin:admin@localhost:5432/ragitect_db"
)

DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"


@dataclass
class DBConfig:
    """Configuration for database settings

    Attributes:
        url: Database connection URL
        pool_size: Number of connections to keep in pool
        max_overflow: Maximum number of connections to create above pool_size
        pool_timeout: Seconds to wait before giving up on getting a connection
        pool_recycle: Recycle connections after N seconds
        echo: Enable SQLAlchemy echo for debugging
    """

    url: str = "postgresql+asyncpg://admin:admin@localhost:5432/ragitect_db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


def load_db_config() -> DBConfig:
    """Load database configuration from environment variables

    Returns:
        DBConfig with values from env vars or defaults
    """
    return DBConfig(
        url=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://admin:admin@localhost:5432/ragitect_db",
        ),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )
