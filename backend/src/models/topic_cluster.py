"""TopicCluster model - Grouped related content."""
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.core.database import Base


class TopicCluster(Base):
    """Groups related source content into topics."""

    __tablename__ = "topic_cluster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_key = Column(String(100), nullable=False, unique=True, index=True)
    embedding_vector = Column(LargeBinary, nullable=True)  # Pickled numpy array
    clustered_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    source_count = Column(Integer, default=0)
    archived = Column(Boolean, default=False, index=True)

    # Relationships
    sources = relationship("SourceContent", backref="cluster", foreign_keys="SourceContent.cluster_id")

    def __repr__(self):
        return f"<TopicCluster(id={self.id}, cluster_key={self.cluster_key}, source_count={self.source_count})>"
