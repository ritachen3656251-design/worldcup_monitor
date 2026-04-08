"""Database connection and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from typing import Generator

from src.core.config import get_config
from src.core.logging import get_logger

logger = get_logger(__name__)

# Database URL
DATABASE_DIR = Path(__file__).parent.parent.parent / "data"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Use dry-run database if enabled
config = get_config()
db_name = "worldcup_dryrun.db" if config.dry_run.enabled else "worldcup.db"
DATABASE_URL = f"sqlite:///{DATABASE_DIR / db_name}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multi-threaded access
        "timeout": 30,  # 30-second lock timeout
    },
    pool_pre_ping=True,  # Verify connections before use
    echo=False,  # Disable SQL logging in production
)


# Enable WAL mode for better concurrency
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better performance."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.close()


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session (dependency injection for FastAPI).

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database (create all tables and indexes).
    """
    logger.info("Initializing database", database_url=DATABASE_URL)

    # Import all models to register them with Base
    from src.models import source_content, topic_cluster, hot_card, detail_page, health_status, api_call_log

    # Create all tables
    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized successfully")


def get_session() -> Session:
    """
    Get a new database session (for non-FastAPI contexts).

    Returns:
        Database session
    """
    return SessionLocal()
