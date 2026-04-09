"""Push notification service - new card detection."""
from datetime import datetime
from typing import List

from sqlalchemy import and_

from src.core.database import get_session
from src.core.logging import get_logger
from src.models.hot_card import HotCard
from src.models.topic_cluster import TopicCluster

logger = get_logger(__name__)


def get_new_cards(since: datetime, category: str = "全部") -> List[HotCard]:
    """
    Get hot cards generated after a given timestamp.

    Args:
        since: Only return cards generated after this time
        category: Optional category filter

    Returns:
        List of new HotCard objects
    """
    session = get_session()

    try:
        query = session.query(HotCard).join(
            TopicCluster,
            HotCard.cluster_id == TopicCluster.id,
        ).filter(
            and_(
                HotCard.generated_at > since,
                TopicCluster.archived == False,
            )
        )

        if category not in ("全部",):
            if category == "热门":
                query = query.order_by(HotCard.hotness_score.desc())
            else:
                query = query.filter(HotCard.category == category)

        query = query.order_by(HotCard.generated_at.desc())
        return query.all()

    finally:
        session.close()
