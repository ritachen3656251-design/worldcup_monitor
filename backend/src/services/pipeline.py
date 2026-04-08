"""Main pipeline orchestration."""
from typing import List
from datetime import datetime

from src.scrapers.hupu import scrape_hupu
from src.models.source_content import SourceContent
from src.utils.text import clean_text
from src.utils.hash import generate_fingerprint
from src.core.database import get_session
from src.core.config import get_config
from src.core.logging import get_logger, log_pipeline_stage

logger = get_logger(__name__)


@log_pipeline_stage("scrape_and_store")
def scrape_and_store() -> List[SourceContent]:
    """
    Scrape content from sources and store in database.

    Pipeline: scrape → clean → fingerprint → deduplicate → store

    Returns:
        List of stored SourceContent objects
    """
    config = get_config()
    session = get_session()

    stored_items = []

    try:
        # Get first keyword for Spec 1 (single keyword)
        keyword = config.scraping.keywords[0] if config.scraping.keywords else "2026世界杯"

        logger.info("Starting scraping pipeline", keyword=keyword)

        # Scrape Hupu (Spec 1: single source)
        scraped_data = scrape_hupu(keyword=keyword, limit=20)

        logger.info("Scraped data", count=len(scraped_data))

        # Process each scraped item
        for item in scraped_data:
            try:
                # Clean text
                cleaned_text = clean_text(item["raw_html"])

                # Generate fingerprint for deduplication
                fingerprint = generate_fingerprint(item["title"], cleaned_text)

                # Check if already exists
                existing = session.query(SourceContent).filter_by(fingerprint=fingerprint).first()
                if existing:
                    logger.info("Duplicate content skipped", fingerprint=fingerprint, title=item["title"][:30])
                    continue

                # Create SourceContent object
                source_content = SourceContent(
                    platform=item["platform"],
                    url=item["url"],
                    title=item["title"],
                    raw_html=item["raw_html"],
                    cleaned_text=cleaned_text,
                    author=item.get("author"),
                    published_at=item["published_at"],
                    interaction_count=item.get("interaction_count", 0),
                    image_urls=str(item.get("image_urls", [])),  # Convert list to string
                    fingerprint=fingerprint,
                    scraped_at=datetime.now(),
                )

                session.add(source_content)
                stored_items.append(source_content)

                logger.info(
                    "Content stored",
                    platform=item["platform"],
                    title=item["title"][:30],
                    fingerprint=fingerprint,
                )

            except Exception as e:
                logger.error("Failed to process scraped item", error=str(e), exc_info=True)
                continue

        # Commit all changes
        session.commit()

        logger.info("Scraping pipeline completed", stored_count=len(stored_items))

    except Exception as e:
        logger.error("Scraping pipeline failed", error=str(e), exc_info=True)
        session.rollback()
        raise

    finally:
        session.close()

    return stored_items
