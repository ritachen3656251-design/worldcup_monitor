"""SourceContent model - Raw scraped data."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime

from src.core.database import Base


class SourceContent(Base):
    """Raw and cleaned scraped content from all sources."""

    __tablename__ = "source_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    raw_html = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=False)
    author = Column(String(200), nullable=True)
    published_at = Column(DateTime, nullable=False)
    interaction_count = Column(Integer, default=0)
    image_urls = Column(Text, nullable=True)  # JSON array string
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)
    scraped_at = Column(DateTime, nullable=False, default=func.now())
    relevance_score = Column(Integer, nullable=True)
    cluster_id = Column(Integer, ForeignKey("topic_cluster.id"), nullable=True, index=True)
    archived = Column(Boolean, default=False, index=True)

    def __repr__(self):
        return f"<SourceContent(id={self.id}, platform={self.platform}, title={self.title[:30]})>"
