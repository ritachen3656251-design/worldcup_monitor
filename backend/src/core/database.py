"""Database connection and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from pathlib import Path
from typing import Generator, Optional

from src.core.config import get_config
from src.core.logging import get_logger

logger = get_logger(__name__)

# Base class for models
class Base(DeclarativeBase):
    pass

# Lazy-initialized globals
_engine = None
_SessionLocal = None

DATABASE_DIR = Path(__file__).parent.parent.parent / "data"


def _get_engine():
    """Lazy-initialize the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        config = get_config()
        db_name = "worldcup_dryrun.db" if config.dry_run.enabled else "worldcup.db"
        database_url = f"sqlite:///{DATABASE_DIR / db_name}"

        _engine = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
            },
            pool_pre_ping=True,
            echo=False,
        )

        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")
            cursor.close()

        logger.info("Database engine created", database=database_url)

    return _engine


def _get_session_factory():
    """Lazy-initialize the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Get database session (dependency injection for FastAPI).

    Yields:
        Database session
    """
    SessionLocal = _get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database (create all tables and indexes)."""
    engine = _get_engine()
    logger.info("Initializing database")

    # Import all models to register them with Base
    from src.models import source_content, topic_cluster, hot_card, detail_page, health_status, api_call_log

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def get_session() -> Session:
    """
    Get a new database session (for non-FastAPI contexts).

    Returns:
        Database session
    """
    SessionLocal = _get_session_factory()
    return SessionLocal()
