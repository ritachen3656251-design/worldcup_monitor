"""懂球帝 scraper - Scrapes articles and posts from DongQiuDi."""
from typing import List, Dict, Any
from datetime import datetime
import re

from src.scrapers.base import unified_request
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_source_content

logger = get_logger(__name__)


def scrape_dongqiudi(keyword: str = "2026世界杯", limit: int = 20) -> List[Dict[str, Any]]:
    """
    Scrape hot posts from 懂球帝.

    Args:
        keyword: Search keyword
        limit: Maximum number of posts to scrape

    Returns:
        List of scraped content dicts
    """
    config = get_config()

    # Dry-run mode: return mock data filtered for dongqiudi
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock data for 懂球帝")
        mock_data = generate_mock_source_content(limit)
        return [item for item in mock_data if item["platform"] == "dongqiudi"][:limit] or mock_data[:limit // 3]

    results = []

    try:
        # DongQiuDi search API
        url = f"https://www.dongqiudi.com/search?keyword={keyword}"
        logger.info("Scraping 懂球帝", url=url, keyword=keyword)

        response = unified_request(url, platform="dongqiudi")

        if response is None or response.status_code != 200:
            logger.warning("懂球帝 request failed", status_code=getattr(response, 'status_code', None))
            return results

        # Parse HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "lxml")

        # Find article items (selectors need verification against actual HTML)
        articles = soup.select("div.article-item, div.search-result-item, article")[:limit]

        for article in articles:
            try:
                # Extract title
                title_el = article.select_one("h3, h2, a.title, .article-title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                # Extract URL
                link_el = article.select_one("a[href]")
                article_url = link_el["href"] if link_el else ""
                if article_url and not article_url.startswith("http"):
                    article_url = f"https://www.dongqiudi.com{article_url}"

                # Extract author
                author_el = article.select_one(".author, .user-name, span.name")
                author = author_el.get_text(strip=True) if author_el else None

                # Extract time
                time_el = article.select_one("time, .time, .date, span.published-at")
                published_at = _parse_dqd_time(time_el.get_text(strip=True)) if time_el else datetime.now()

                # Extract content/snippet
                content_el = article.select_one("p, .summary, .content, .desc")
                raw_html = str(article)
                cleaned_text = content_el.get_text(strip=True) if content_el else title

                # Extract interaction count
                comment_el = article.select_one(".comment-count, .comments, .interaction")
                interaction = 0
                if comment_el:
                    nums = re.findall(r'\d+', comment_el.get_text())
                    interaction = int(nums[0]) if nums else 0

                results.append({
                    "platform": "dongqiudi",
                    "url": article_url,
                    "title": title,
                    "raw_html": raw_html,
                    "cleaned_text": cleaned_text,
                    "author": author,
                    "published_at": published_at,
                    "interaction_count": interaction,
                    "image_urls": [],
                })

            except Exception as e:
                logger.error("Failed to parse 懂球帝 article", error=str(e))
                continue

        logger.info("懂球帝 scraping done", results_count=len(results))

    except Exception as e:
        logger.error("懂球帝 scraping failed", error=str(e), exc_info=True)

    return results


def _parse_dqd_time(time_str: str) -> datetime:
    """Parse 懂球帝 time string to datetime."""
    try:
        if "分钟前" in time_str:
            from datetime import timedelta
            minutes = int(re.findall(r'\d+', time_str)[0])
            return datetime.now() - timedelta(minutes=minutes)
        elif "小时前" in time_str:
            from datetime import timedelta
            hours = int(re.findall(r'\d+', time_str)[0])
            return datetime.now() - timedelta(hours=hours)
        elif "天前" in time_str:
            from datetime import timedelta
            days = int(re.findall(r'\d+', time_str)[0])
            return datetime.now() - timedelta(days=days)
        else:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m-%d %H:%M"]:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            return datetime.now()
    except Exception:
        return datetime.now()
