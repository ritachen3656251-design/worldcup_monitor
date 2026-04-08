"""HotCard model - AI-generated card summaries."""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from src.core.database import Base


class HotCard(Base):
    """AI-generated card summaries for display in discovery feed."""

    __tablename__ = "hot_card"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, ForeignKey("topic_cluster.id"), nullable=False, unique=True, index=True)
    title = Column(String(50), nullable=False)
    summary = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    credibility = Column(String(20), nullable=False)
    source_labels = Column(Text, nullable=False)  # JSON array string
    image_url = Column(Text, nullable=True)
    hotness_score = Column(Float, nullable=False, index=True)
    generated_at = Column(DateTime, nullable=False, default=func.now())
    cached_until = Column(DateTime, nullable=False, index=True)

    def __repr__(self):
        return f"<HotCard(id={self.id}, title={self.title}, category={self.category})>"
