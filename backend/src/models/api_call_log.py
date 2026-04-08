"""APICallLog model - API usage tracking."""
from sqlalchemy import Column, Integer, Date, DateTime
from sqlalchemy.sql import func

from src.core.database import Base


class APICallLog(Base):
    """Tracks daily API call counts for rate limiting."""

    __tablename__ = "api_call_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    call_count = Column(Integer, default=0)
    limit = Column(Integer, nullable=False)
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<APICallLog(date={self.date}, call_count={self.call_count}, limit={self.limit})>"
