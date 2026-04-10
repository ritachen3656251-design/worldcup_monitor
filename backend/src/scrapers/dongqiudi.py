"""懂球帝 scraper - Fetches articles from DongQiuDi app API."""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote

from bs4 import BeautifulSoup

from src.scrapers.base import unified_request
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_source_content

logger = get_logger(__name__)

# DongQiuDi tab IDs with World Cup content
WORLDCUP_TAB_ID = 114  # [世界杯] dedicated tab


def scrape_dongqiudi(keyword: str = "2026世界杯", limit: int = None) -> List[Dict[str, Any]]:
    """
    Scrape articles from 懂球帝 app API.

    Uses the World Cup dedicated tab (tab 114) which returns
    curated World Cup content. Falls back to recommended feed
    (tab 1) with keyword filtering if the WC tab is empty.

    Args:
        keyword: Search keyword (used for fallback filtering)
        limit: Maximum number of articles to return (default: from config)

    Returns:
        List of scraped content dicts
    """
    config = get_config()

    # Use config limit if not specified
    if limit is None:
        limit = getattr(config.scraping, "limit_per_source", 20)

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


def _fetch_article_content(url: str) -> Optional[str]:
    """
    Fetch article full content from DongQiuDi web page.

    Args:
        url: Article web page URL (mobile or desktop)

    Returns:
        Article content text, or None if failed
    """
    try:
        # Convert mobile URL to desktop URL for better content extraction
        # Mobile: https://n.dongqiudi.com/webapp/news.html?articleId=5768662&from=tab_114
        # Desktop: https://www.dongqiudi.com/article/5768662
        if "n.dongqiudi.com/webapp/news.html" in url and "articleId=" in url:
            import re
            match = re.search(r'articleId=(\d+)', url)
            if match:
                article_id = match.group(1)
                url = f"https://www.dongqiudi.com/article/{article_id}"
                logger.info("Converted mobile URL to desktop", article_id=article_id)

        logger.info("Fetching article content from web", url=url)
        response = unified_request(url, platform="dongqiudi")
        soup = BeautifulSoup(response.text, "lxml")

        # Extract main content from <div class="con">
        con_elem = soup.find("div", class_="con")
        if not con_elem:
            logger.warning("No content div found", url=url)
            return None

        # Remove hidden elements (like video placeholders)
        for hidden in con_elem.find_all(style="display:none;"):
            hidden.decompose()

        # Extract all paragraphs
        paragraphs = con_elem.find_all("p")
        content_parts = []

        for p in paragraphs:
            # Skip image captions
            if "img-tips" in p.get("class", []):
                continue

            text = p.get_text(strip=True)
            # Skip very short paragraphs (likely not content)
            if text and len(text) > 10:
                content_parts.append(text)

        if not content_parts:
            logger.warning("No content paragraphs found", url=url)
            return None

        content = "\n\n".join(content_parts)
        logger.info("Article content fetched", url=url, length=len(content))
        return content

    except Exception as e:
        logger.error("Failed to fetch article content", url=url, error=str(e))
        return None


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

    # Fetch full article content from web page
    cleaned_text = ""
    if url:
        web_content = _fetch_article_content(url)
        if web_content:
            cleaned_text = web_content
        else:
            # Fallback: use description from API
            description = article.get("description", "") or article.get("b_description", "")
            cleaned_text = description if description else title
            logger.warning("Using API description as fallback", article_id=article_id)
    else:
        # No URL, use description
        description = article.get("description", "") or article.get("b_description", "")
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
