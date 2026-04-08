"""DetailPage model - AI-generated detailed content."""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from src.core.database import Base


class DetailPage(Base):
    """AI-generated detailed content for individual topics."""

    __tablename__ = "detail_page"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("topic_cluster.id"), nullable=False, unique=True, index=True)
    overview = Column(Text, nullable=False)
    viewpoints = Column(Text, nullable=False)  # JSON array string
    timeline = Column(Text, nullable=False)  # JSON array string
    sources = Column(Text, nullable=False)  # JSON array string
    generated_at = Column(DateTime, nullable=False, default=func.now())
    cached_until = Column(DateTime, nullable=False, index=True)

    def __repr__(self):
        return f"<DetailPage(id={self.id}, cluster_id={self.cluster_id})>"
