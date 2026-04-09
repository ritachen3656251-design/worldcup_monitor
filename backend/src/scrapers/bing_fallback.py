"""Bing Search API fallback scraper."""
from typing import List, Dict, Any
from datetime import datetime
import re

from src.core.config import get_config
from src.core.logging import get_logger

logger = get_logger(__name__)


def scrape_bing_fallback(keyword: str = "2026世界杯", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search Bing for World Cup content as a fallback when primary sources fail.

    All Bing-sourced content is marked as "待确认" credibility and labeled "搜索引擎聚合".

    Args:
        keyword: Search keyword
        limit: Maximum number of results

    Returns:
        List of scraped content dicts
    """
    config = get_config()

    # Dry-run mode
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock data for Bing fallback")
        from src.utils.mock import generate_mock_source_content
        mock_data = generate_mock_source_content(limit)
        for item in mock_data:
            item["platform"] = "bing"
        return mock_data[:limit]

    results = []
    api_key = config.bing_search_api_key

    if not api_key:
        logger.warning("Bing Search API key not configured, skipping fallback")
        return results

    try:
        import requests

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
        }
        params = {
            "q": f"{keyword} site:sports.sina.com.cn OR site:sohu.com/sports OR site:163.com/sports",
            "count": limit,
            "mkt": "zh-CN",
            "freshness": "Week",
        }

        logger.info("Bing fallback search", keyword=keyword)
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code != 200:
            logger.warning("Bing API request failed", status_code=response.status_code)
            return results

        data = response.json()
        web_pages = data.get("webPages", {}).get("value", [])

        for page in web_pages[:limit]:
            try:
                title = page.get("name", "")
                snippet = page.get("snippet", "")
                page_url = page.get("url", "")
                date_published = page.get("dateLastCrawled", "")

                # Parse date
                published_at = datetime.now()
                if date_published:
                    try:
                        published_at = datetime.fromisoformat(date_published.replace("Z", "+00:00"))
                    except Exception:
                        pass

                results.append({
                    "platform": "bing",
                    "url": page_url,
                    "title": title,
                    "raw_html": snippet,
                    "cleaned_text": snippet,
                    "author": "搜索引擎聚合",
                    "published_at": published_at,
                    "interaction_count": 0,
                    "image_urls": [],
                })

            except Exception as e:
                logger.error("Failed to parse Bing result", error=str(e))
                continue

        logger.info("Bing fallback done", results_count=len(results))

    except Exception as e:
        logger.error("Bing fallback search failed", error=str(e), exc_info=True)

    return results
