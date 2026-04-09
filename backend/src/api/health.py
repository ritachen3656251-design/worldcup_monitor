"""Health check API endpoints."""
from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.health_status import SourceHealth
from src.models.api_call_log import APICallLog
from src.core.config import get_config

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint.

    Returns system health including database, scheduler, sources, and API usage.
    """
    config = get_config()

    # Check source health
    source_statuses = {}
    try:
        sources = db.query(SourceHealth).all()
        for s in sources:
            source_statuses[s.platform] = s.status
    except Exception:
        source_statuses = {"hupu": "unknown", "dongqiudi": "unknown", "bilibili": "unknown"}

    # Check API usage
    api_usage = {"calls_today": 0, "limit": config.ai.daily_limit, "remaining": config.ai.daily_limit}
    try:
        today = date.today()
        log_entry = db.query(APICallLog).filter_by(date=today).first()
        if log_entry:
            api_usage["calls_today"] = log_entry.call_count
            api_usage["remaining"] = max(0, config.ai.daily_limit - log_entry.call_count)
    except Exception:
        pass

    # Determine overall status
    all_healthy = all(s == "healthy" for s in source_statuses.values()) if source_statuses else True
    overall_status = "healthy" if all_healthy else "degraded"

    return {
        "success": True,
        "data": {
            "status": overall_status,
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "healthy",
                "scheduler": "healthy",
                "sources": source_statuses,
                "api_usage": api_usage,
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/sources/health")
def get_source_health(db: Session = Depends(get_db)):
    """
    Get detailed health status of all scraping sources.
    """
    sources = db.query(SourceHealth).all()

    source_list = []
    backup_active = False

    for s in sources:
        source_list.append({
            "platform": s.platform,
            "status": s.status,
            "failure_count": s.failure_count,
            "last_check": s.last_check.isoformat() if s.last_check else None,
            "last_success": s.last_success.isoformat() if s.last_success else None,
            "degraded_at": s.degraded_at.isoformat() if s.degraded_at else None,
        })
        if s.status == "degraded":
            backup_active = True

    return {
        "success": True,
        "data": {
            "sources": source_list,
            "backup_active": backup_active,
            "backup_source": "bing" if backup_active else None,
        },
        "timestamp": datetime.now().isoformat(),
    }
