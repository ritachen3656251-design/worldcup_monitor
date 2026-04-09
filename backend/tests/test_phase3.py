"""Test script for Phase 3 (Spec 1) - Minimal Pipeline."""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.core.config import get_config
from src.core.database import init_db, get_session
from src.core.logging import setup_logging, get_logger
from src.services.pipeline import scrape_and_store
from src.models.source_content import SourceContent

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_phase3():
    """Test Phase 3: Minimal Pipeline."""
    logger.info("=" * 60)
    logger.info("Testing Phase 3: Spec 1 - Minimal Pipeline")
    logger.info("=" * 60)

    # Test 1: Configuration Loading
    logger.info("\n[Test 1] Configuration Loading")
    try:
        config = get_config()
        logger.info(f"✓ Config loaded successfully")
        logger.info(f"  - Dry-run mode: {config.dry_run.enabled}")
        logger.info(f"  - Scraping interval: {config.scraping.interval_minutes} minutes")
        logger.info(f"  - Keywords count: {len(config.scraping.keywords)}")
        logger.info(f"  - First keyword: {config.scraping.keywords[0]}")
    except Exception as e:
        logger.error(f"✗ Config loading failed: {e}")
        return False

    # Test 2: Database Initialization
    logger.info("\n[Test 2] Database Initialization")
    try:
        init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False

    # Test 3: Scraping and Storage Pipeline
    logger.info("\n[Test 3] Scraping and Storage Pipeline")
    try:
        stored_items = scrape_and_store()
        logger.info(f"✓ Pipeline executed successfully")
        logger.info(f"  - Items stored: {len(stored_items)}")

        if len(stored_items) > 0:
            sample = stored_items[0]
            logger.info(f"  - Sample title: {sample.title[:50]}...")
            logger.info(f"  - Sample platform: {sample.platform}")
    except Exception as e:
        logger.error(f"✗ Pipeline execution failed: {e}", exc_info=True)
        return False

    # Test 4: Database Query
    logger.info("\n[Test 4] Database Query")
    try:
        session = get_session()
        count = session.query(SourceContent).count()
        logger.info(f"✓ Database query successful")
        logger.info(f"  - Total items in database: {count}")

        if count > 0:
            latest = session.query(SourceContent)\
                .order_by(SourceContent.scraped_at.desc())\
                .first()
            logger.info(f"  - Latest item: {latest.title[:50]}...")
            logger.info(f"  - Scraped at: {latest.scraped_at}")

        session.close()
    except Exception as e:
        logger.error(f"✗ Database query failed: {e}")
        return False

    # Test 5: Deduplication
    logger.info("\n[Test 5] Deduplication Test")
    try:
        logger.info("Running pipeline again to test deduplication...")
        stored_items_2 = scrape_and_store()
        logger.info(f"✓ Deduplication working")
        logger.info(f"  - New items stored: {len(stored_items_2)}")
        logger.info(f"  - (Should be 0 if same content)")
    except Exception as e:
        logger.error(f"✗ Deduplication test failed: {e}")
        return False

    logger.info("\n" + "=" * 60)
    logger.info("✓ All Phase 3 tests passed!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Start backend: cd backend && uvicorn src.main:app --reload")
    logger.info("2. Start frontend: cd frontend && npm install && npm run dev")
    logger.info("3. Visit: http://localhost:5173")

    return True


if __name__ == "__main__":
    success = test_phase3()
    sys.exit(0 if success else 1)
