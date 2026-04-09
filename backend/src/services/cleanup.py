"""Scheduled cleanup job for archiving and deleting old content."""
from datetime import datetime, timedelta, date

from sqlalchemy import and_

from src.core.config import get_config
from src.core.database import get_session
from src.core.logging import get_logger
from src.models.source_content import SourceContent
from src.models.topic_cluster import TopicCluster
from src.models.hot_card import HotCard
from src.models.detail_page import DetailPage
from src.models.api_call_log import APICallLog

logger = get_logger(__name__)


def run_cleanup():
    """
    Run scheduled cleanup job.

    Per FR-004:
    - Archive content after 72 hours if low hotness
    - Delete archived content after 30 days
    - Delete old API call logs after 30 days

    Runs daily at 2 AM.
    """
    config = get_config()
    session = get_session()

    try:
        now = datetime.now()
        archive_threshold = now - timedelta(hours=config.content.archive_after_hours)
        delete_threshold = now - timedelta(days=config.content.retention_days)

        # Step 1: Archive old content with low hotness
        archived_count = 0
        old_content = session.query(SourceContent).filter(
            and_(
                SourceContent.archived == False,
                SourceContent.scraped_at < archive_threshold,
            )
        ).all()

        for item in old_content:
            # Check if the associated card has low hotness
            if item.cluster_id:
                card = session.query(HotCard).filter_by(cluster_id=item.cluster_id).first()
                if card and card.hotness_score < config.content.hotness_threshold:
                    item.archived = True
                    archived_count += 1
            else:
                # No cluster = no card = archive
                item.archived = True
                archived_count += 1

        session.commit()
        logger.info("Content archived", count=archived_count)

        # Step 2: Archive clusters where all sources are archived
        clusters = session.query(TopicCluster).filter(
            TopicCluster.archived == False,
        ).all()

        clusters_archived = 0
        for cluster in clusters:
            sources = session.query(SourceContent).filter_by(
                cluster_id=cluster.id,
                archived=False,
            ).count()
            if sources == 0:
                cluster.archived = True
                clusters_archived += 1

        session.commit()
        logger.info("Clusters archived", count=clusters_archived)

        # Step 3: Delete old archived content (>30 days)
        deleted_content = session.query(SourceContent).filter(
            and_(
                SourceContent.archived == True,
                SourceContent.scraped_at < delete_threshold,
            )
        ).delete(synchronize_session=False)

        # Delete orphaned clusters
        deleted_clusters = session.query(TopicCluster).filter(
            and_(
                TopicCluster.archived == True,
                TopicCluster.clustered_at < delete_threshold,
            )
        ).delete(synchronize_session=False)

        # Delete old API call logs
        log_threshold = date.today() - timedelta(days=config.content.retention_days)
        deleted_logs = session.query(APICallLog).filter(
            APICallLog.date < log_threshold,
        ).delete(synchronize_session=False)

        session.commit()

        logger.info(
            "Cleanup completed",
            archived_content=archived_count,
            archived_clusters=clusters_archived,
            deleted_content=deleted_content,
            deleted_clusters=deleted_clusters,
            deleted_logs=deleted_logs,
        )

    except Exception as e:
        logger.error("Cleanup job failed", error=str(e), exc_info=True)
        session.rollback()

    finally:
        session.close()
