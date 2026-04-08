"""SourceHealth model - Health monitoring for scraping sources."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from src.core.database import Base


class SourceHealth(Base):
    """Tracks health status of scraping sources for monitoring and degradation."""

    __tablename__ = "source_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, index=True)  # healthy, degraded, failed
    failure_count = Column(Integer, default=0)
    last_check = Column(DateTime, nullable=False)
    last_success = Column(DateTime, nullable=True)
    degraded_at = Column(DateTime, nullable=True)
    alert_sent = Column(Boolean, default=False)

    def __repr__(self):
        return f"<SourceHealth(platform={self.platform}, status={self.status}, failure_count={self.failure_count})>"
