"""虎扑 (Hupu) scraper."""
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from src.scrapers.base import unified_request
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_source_content

logger = get_logger(__name__)


def scrape_hupu(keyword: str = "2026世界杯", limit: int = 20) -> List[Dict[str, Any]]:
    """
    Scrape 虎扑 hot posts for a given keyword.

    Args:
        keyword: Search keyword (default: "2026世界杯")
        limit: Maximum number of posts to scrape (default: 20)

    Returns:
        List of scraped content dicts
    """
    config = get_config()

    # Check dry-run mode
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock data for Hupu scraper")
        mock_data = generate_mock_source_content(limit)
        return [item for item in mock_data if item["platform"] == "hupu"][:limit]

    logger.info("Scraping Hupu", keyword=keyword, limit=limit)

    results = []

    try:
        # Hupu search URL (using their search API or hot posts page)
        # Note: This is a simplified implementation. Real implementation would need
        # to handle Hupu's actual URL structure and pagination
        search_url = f"https://bbs.hupu.com/search?q={keyword}"

        response = unified_request(search_url, platform="hupu")

        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')

        # Find post items (adjust selectors based on actual Hupu HTML structure)
        # This is a placeholder - actual selectors need to be determined by inspecting Hupu's HTML
        post_items = soup.find_all('div', class_='post-item', limit=limit)

        for item in post_items:
            try:
                # Extract post data (adjust based on actual HTML structure)
                title_elem = item.find('a', class_='post-title')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = f"https://bbs.hupu.com{url}"

                # Extract author
                author_elem = item.find('span', class_='author')
                author = author_elem.get_text(strip=True) if author_elem else "未知用户"

                # Extract interaction count (likes + comments)
                interaction_elem = item.find('span', class_='interaction')
                interaction_count = 0
                if interaction_elem:
                    try:
                        interaction_count = int(interaction_elem.get_text(strip=True))
                    except ValueError:
                        pass

                # Extract publish time
                time_elem = item.find('span', class_='time')
                published_at = datetime.now()  # Default to now
                if time_elem:
                    time_str = time_elem.get_text(strip=True)
                    # Parse time string (e.g., "2小时前", "2026-04-08 10:00")
                    # This is simplified - real implementation needs proper time parsing
                    published_at = _parse_hupu_time(time_str)

                # Extract images
                image_urls = []
                img_elems = item.find_all('img', class_='post-image')
                for img in img_elems:
                    img_url = img.get('src', '')
                    if img_url:
                        image_urls.append(img_url)

                # Get full post content by visiting the post URL
                raw_html = str(item)

                results.append({
                    "platform": "hupu",
                    "url": url,
                    "title": title,
                    "raw_html": raw_html,
                    "author": author,
                    "published_at": published_at,
                    "interaction_count": interaction_count,
                    "image_urls": image_urls,
                })

            except Exception as e:
                logger.warning("Failed to parse Hupu post item", error=str(e))
                continue

        logger.info("Hupu scraping completed", keyword=keyword, results_count=len(results))

    except Exception as e:
        logger.error("Hupu scraping failed", keyword=keyword, error=str(e), exc_info=True)

    return results


def _parse_hupu_time(time_str: str) -> datetime:
    """
    Parse Hupu time string to datetime.

    Args:
        time_str: Time string from Hupu (e.g., "2小时前", "2026-04-08 10:00")

    Returns:
        Parsed datetime
    """
    from datetime import timedelta
    import re

    # Handle relative time (e.g., "2小时前", "3天前")
    if "分钟前" in time_str:
        match = re.search(r'(\d+)分钟前', time_str)
        if match:
            minutes = int(match.group(1))
            return datetime.now() - timedelta(minutes=minutes)

    if "小时前" in time_str:
        match = re.search(r'(\d+)小时前', time_str)
        if match:
            hours = int(match.group(1))
            return datetime.now() - timedelta(hours=hours)

    if "天前" in time_str:
        match = re.search(r'(\d+)天前', time_str)
        if match:
            days = int(match.group(1))
            return datetime.now() - timedelta(days=days)

    # Handle absolute time (e.g., "2026-04-08 10:00")
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        pass

    # Default to now if parsing fails
    return datetime.now()
