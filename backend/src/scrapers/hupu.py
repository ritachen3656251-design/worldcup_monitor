"""虎扑 (Hupu) scraper - Extracts search results from embedded JSON data."""
import json
import re
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import quote

from src.scrapers.base import unified_request
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_source_content

logger = get_logger(__name__)


def scrape_hupu(keyword: str = "2026世界杯", limit: int = None) -> List[Dict[str, Any]]:
    """
    Scrape 虎扑 search results for a given keyword.

    Hupu embeds search data as JSON in window.$$data within the HTML.
    We extract and parse this JSON directly instead of scraping DOM nodes.

    Args:
        keyword: Search keyword (default: "2026世界杯")
        limit: Maximum number of posts to return (default: from config)

    Returns:
        List of scraped content dicts
    """
    config = get_config()

    # Use config limit if not specified
    if limit is None:
        limit = getattr(config.scraping, "limit_per_source", 20)

    # Check dry-run mode
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock data for Hupu scraper")
        mock_data = generate_mock_source_content(limit)
        return [item for item in mock_data if item["platform"] == "hupu"][:limit]

    logger.info("Scraping Hupu", keyword=keyword, limit=limit)

    results = []

    try:
        search_url = f"https://bbs.hupu.com/search?q={quote(keyword)}"
        response = unified_request(search_url, platform="hupu")
        html = response.text

        # Extract window.$$data JSON from the page
        items = _extract_search_data(html)
        if items is None:
            logger.warning("Failed to extract search data from Hupu page")
            return results

        logger.info("Hupu raw items extracted", count=len(items))

        for item in items[:limit]:
            try:
                parsed = _parse_item(item)
                if parsed:
                    results.append(parsed)
            except Exception as e:
                logger.warning("Failed to parse Hupu item", error=str(e))
                continue

        logger.info("Hupu scraping completed", keyword=keyword, results_count=len(results))

    except Exception as e:
        logger.error("Hupu scraping failed", keyword=keyword, error=str(e), exc_info=True)

    return results


def _extract_search_data(html: str) -> list | None:
    """
    Extract search result items from window.$$data JSON embedded in HTML.

    Returns:
        List of raw item dicts, or None if extraction fails
    """
    marker = "window.$$data="
    start = html.find(marker)
    if start < 0:
        return None

    json_start = start + len(marker)

    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(html, json_start)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Hupu JSON", error=str(e))
        return None

    search_res = data.get("searchRes", {})
    items = search_res.get("data", [])
    return items


def _parse_item(item: dict) -> dict | None:
    """
    Parse a single search result item into our standard format.

    Args:
        item: Raw item dict from Hupu JSON

    Returns:
        Standardized content dict, or None if essential fields are missing
    """
    # Title: strip HTML highlight tags
    raw_title = item.get("title", "")
    if not raw_title:
        return None
    title = _strip_html_tags(raw_title)

    # Content: strip HTML highlight tags
    raw_content = item.get("content", "")
    content = _strip_html_tags(raw_content) if raw_content else title

    # Post URL
    post_id = item.get("id", "")
    url = f"https://bbs.hupu.com/{post_id}.html" if post_id else ""

    # Author
    author = item.get("username", "未知用户")

    # Publish time (unix timestamp string)
    addtime = item.get("addtime", "")
    if addtime:
        try:
            published_at = datetime.fromtimestamp(int(addtime))
        except (ValueError, OSError):
            published_at = datetime.now()
    else:
        published_at = datetime.now()

    # Interaction count: replies + lights
    replies = _safe_int(item.get("replies", "0"))
    lights = _safe_int(item.get("lights", "0"))
    interaction_count = replies + lights

    # Image
    image_urls = []
    picture = item.get("picture", "")
    if picture and isinstance(picture, str) and picture.startswith("http"):
        image_urls.append(picture)

    # Keep the raw JSON as raw_html for debugging/reprocessing
    raw_html = json.dumps(item, ensure_ascii=False)

    return {
        "platform": "hupu",
        "url": url,
        "title": title,
        "raw_html": raw_html,
        "cleaned_text": content,
        "author": author,
        "published_at": published_at,
        "interaction_count": interaction_count,
        "image_urls": image_urls,
    }


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags from text (e.g. <font color='...'> highlight wrappers)."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _safe_int(val) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
