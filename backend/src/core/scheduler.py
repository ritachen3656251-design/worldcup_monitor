"""APScheduler configuration and setup."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from pathlib import Path

from src.core.config import get_config
from src.core.logging import get_logger

logger = get_logger(__name__)


def create_scheduler() -> BackgroundScheduler:
    """
    Create and configure APScheduler instance.

    Returns:
        Configured BackgroundScheduler
    """
    config = get_config()

    # Job store configuration (SQLite)
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_name = "scheduler_dryrun.db" if config.dry_run.enabled else "scheduler.db"
    jobstore_url = f"sqlite:///{data_dir / db_name}"

    jobstores = {
        'default': SQLAlchemyJobStore(url=jobstore_url)
    }

    # Executor configuration
    executors = {
        'default': ThreadPoolExecutor(max_workers=5)
    }

    # Job defaults
    job_defaults = {
        'coalesce': True,  # Combine missed runs into one
        'max_instances': 1,  # Only one instance of each job at a time
        'misfire_grace_time': 300,  # 5 minutes grace period
    }

    # Create scheduler
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone='Asia/Shanghai',
    )

    logger.info("Scheduler created", jobstore_url=jobstore_url)

    return scheduler


# Global scheduler instance
_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """Get global scheduler instance (singleton)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = create_scheduler()
    return _scheduler


def start_scheduler() -> None:
    """Start the global scheduler."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    """Shutdown the global scheduler."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")
