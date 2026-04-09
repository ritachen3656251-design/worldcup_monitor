"""懂球帝 scraper - Fetches articles from DongQiuDi app API."""
import json
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import quote

from src.scrapers.base import unified_request
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_source_content

logger = get_logger(__name__)

# DongQiuDi tab IDs with World Cup content
WORLDCUP_TAB_ID = 114  # [世界杯] dedicated tab


def scrape_dongqiudi(keyword: str = "2026世界杯", limit: int = 20) -> List[Dict[str, Any]]:
    """
    Scrape articles from 懂球帝 app API.

    Uses the World Cup dedicated tab (tab 114) which returns
    curated World Cup content. Falls back to recommended feed
    (tab 1) with keyword filtering if the WC tab is empty.

    Args:
        keyword: Search keyword (used for fallback filtering)
        limit: Maximum number of articles to return

    Returns:
        List of scraped content dicts
    """
    config = get_config()

    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock data for 懂球帝")
        mock_data = generate_mock_source_content(limit)
        return [item for item in mock_data if item["platform"] == "dongqiudi"][:limit] or mock_data[:limit // 3]

    logger.info("Scraping 懂球帝", keyword=keyword, limit=limit)

    results = []

    try:
        # Primary: World Cup dedicated tab
        articles = _fetch_tab(WORLDCUP_TAB_ID)

        if not articles:
            # Fallback: recommended feed, filtered by keyword
            logger.warning("World Cup tab empty, falling back to recommended feed")
            all_articles = _fetch_tab(1)
            keywords = keyword.split() + ["世界杯", "World Cup"]
            articles = [
                a for a in all_articles
                if any(kw in a.get("title", "") for kw in keywords)
            ]

        logger.info("懂球帝 raw articles fetched", count=len(articles))

        for article in articles[:limit]:
            try:
                parsed = _parse_article(article)
                if parsed:
                    results.append(parsed)
            except Exception as e:
                logger.warning("Failed to parse 懂球帝 article", error=str(e))
                continue

        logger.info("懂球帝 scraping completed", results_count=len(results))

    except Exception as e:
        logger.error("懂球帝 scraping failed", error=str(e), exc_info=True)

    return results


def _fetch_tab(tab_id: int) -> List[dict]:
    """Fetch articles from a DongQiuDi app API tab."""
    url = f"https://api.dongqiudi.com/app/tabs/iphone/{tab_id}.json"

    try:
        response = unified_request(url, platform="dongqiudi")
        data = response.json()
        return data.get("articles", [])
    except Exception as e:
        logger.error("Failed to fetch DongQiuDi tab", tab_id=tab_id, error=str(e))
        return []


def _parse_article(article: dict) -> dict | None:
    """
    Parse a single DongQiuDi article into our standard format.

    Args:
        article: Raw article dict from DongQiuDi API

    Returns:
        Standardized content dict, or None if essential fields missing
    """
    title = article.get("title", "")
    if not title:
        return None

    article_id = article.get("id", "")
    url = article.get("url", "")
    if not url and article_id:
        url = f"https://www.dongqiudi.com/article/{article_id}"

    author = article.get("author_name", "懂球帝")

    # Parse publish time
    time_str = article.get("published_at", "")
    published_at = _parse_time(time_str)

    # Interaction count: comments
    comments = article.get("comments_total", 0)
    try:
        interaction_count = int(comments)
    except (ValueError, TypeError):
        interaction_count = 0

    # Description / content
    description = article.get("description", "") or article.get("b_description", "")
    # If no description, use title as content (DQD API often has empty descriptions)
    cleaned_text = description if description else title

    # Thumbnail image
    image_urls = []
    thumb = article.get("thumb", "")
    if thumb and isinstance(thumb, str) and thumb.startswith("http"):
        image_urls.append(thumb)

    # Keep raw JSON for debugging
    raw_html = json.dumps(article, ensure_ascii=False)

    return {
        "platform": "dongqiudi",
        "url": url,
        "title": title,
        "raw_html": raw_html,
        "cleaned_text": cleaned_text,
        "author": author,
        "published_at": published_at,
        "interaction_count": interaction_count,
        "image_urls": image_urls,
    }


def _parse_time(time_str: str) -> datetime:
    """Parse DongQiuDi time string to datetime."""
    if not time_str:
        return datetime.now()
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return datetime.now()
