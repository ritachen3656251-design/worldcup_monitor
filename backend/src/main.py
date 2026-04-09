"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.config import get_config
from src.core.logging import setup_logging, get_logger
from src.core.database import init_db
from src.core.scheduler import get_scheduler, start_scheduler, shutdown_scheduler
from src.services.pipeline import scrape_and_store, run_full_pipeline
from src.services.monitoring import probe_source_health
from src.services.cleanup import run_cleanup
from src.api import cards, health, details

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting World Cup Monitor API")

    # Initialize database
    init_db()

    # Start scheduler
    config = get_config()
    scheduler = get_scheduler()

    # Add pipeline job (every 30 minutes) - full pipeline includes scraping + AI
    scheduler.add_job(
        run_full_pipeline,
        'interval',
        minutes=config.scraping.interval_minutes,
        id='pipeline_job',
        replace_existing=True,
    )

    start_scheduler()
    logger.info("Scheduler started with pipeline and monitoring jobs")

    # Add health monitoring job (every 5 minutes)
    scheduler.add_job(
        probe_source_health,
        'interval',
        minutes=config.monitoring.probe_interval_minutes,
        id='health_monitoring_job',
        replace_existing=True,
    )

    # Add cleanup job (daily at 2 AM)
    scheduler.add_job(
        run_cleanup,
        'cron',
        hour=2,
        minute=0,
        id='cleanup_job',
        replace_existing=True,
    )

    yield

    # Shutdown
    logger.info("Shutting down World Cup Monitor API")
    shutdown_scheduler()


# Create FastAPI app
app = FastAPI(
    title="World Cup Hot Topics Monitor",
    description="AI-powered editorial platform for 2026 World Cup news",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cards.router)
app.include_router(health.router)
app.include_router(details.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "World Cup Hot Topics Monitor API",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
