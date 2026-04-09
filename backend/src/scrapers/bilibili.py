"""B站 scraper - Scrapes videos and dynamics from Bilibili."""
from typing import List, Dict, Any
from datetime import datetime
import re

from src.scrapers.base import unified_request
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_source_content

logger = get_logger(__name__)


def scrape_bilibili(keyword: str = "2026世界杯", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Scrape videos and dynamics from B站 search.

    Args:
        keyword: Search keyword
        limit: Maximum number of items to scrape

    Returns:
        List of scraped content dicts
    """
    config = get_config()

    # Dry-run mode: return mock data filtered for bilibili
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock data for B站")
        mock_data = generate_mock_source_content(limit)
        return [item for item in mock_data if item["platform"] == "bilibili"][:limit] or mock_data[:limit // 3]

    results = []

    try:
        # Bilibili search API (web endpoint)
        url = f"https://search.bilibili.com/all?keyword={keyword}&order=totalrank"
        logger.info("Scraping B站", url=url, keyword=keyword)

        response = unified_request(url, platform="bilibili")

        if response is None or response.status_code != 200:
            logger.warning("B站 request failed", status_code=getattr(response, 'status_code', None))
            return results

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "lxml")

        # Find video items (selectors need verification against actual HTML)
        videos = soup.select("div.video-item, li.video-item, div.bili-video-card")[:limit]

        for video in videos:
            try:
                # Extract title
                title_el = video.select_one("a.title, h3 a, .bili-video-card__info--tit a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                # Extract URL
                video_url = title_el.get("href", "")
                if video_url and not video_url.startswith("http"):
                    video_url = f"https:{video_url}" if video_url.startswith("//") else f"https://www.bilibili.com{video_url}"

                # Extract author/uploader
                author_el = video.select_one(".up-name, .bili-video-card__info--author")
                author = author_el.get_text(strip=True) if author_el else None

                # Extract time
                time_el = video.select_one(".time, .date, .bili-video-card__info--date")
                published_at = _parse_bili_time(time_el.get_text(strip=True)) if time_el else datetime.now()

                # Extract content (title + description)
                desc_el = video.select_one(".desc, .description")
                description = desc_el.get_text(strip=True) if desc_el else ""
                raw_html = str(video)

                # Extract view/play count
                view_el = video.select_one(".play-count, .view-count, .bili-video-card__stats--item")
                interaction = 0
                if view_el:
                    text = view_el.get_text()
                    nums = re.findall(r'[\d.]+', text)
                    if nums:
                        num = float(nums[0])
                        if "万" in text:
                            num *= 10000
                        interaction = int(num)

                # Extract thumbnail
                img_el = video.select_one("img")
                image_urls = []
                if img_el and img_el.get("src"):
                    img_src = img_el["src"]
                    if not img_src.startswith("http"):
                        img_src = f"https:{img_src}"
                    image_urls.append(img_src)

                results.append({
                    "platform": "bilibili",
                    "url": video_url,
                    "title": title,
                    "raw_html": raw_html,
                    "cleaned_text": f"{title} {description}".strip(),
                    "author": author,
                    "published_at": published_at,
                    "interaction_count": interaction,
                    "image_urls": image_urls,
                })

            except Exception as e:
                logger.error("Failed to parse B站 video", error=str(e))
                continue

        logger.info("B站 scraping done", results_count=len(results))

    except Exception as e:
        logger.error("B站 scraping failed", error=str(e), exc_info=True)

    return results


def _parse_bili_time(time_str: str) -> datetime:
    """Parse B站 time string to datetime."""
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
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m-%d"]:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            return datetime.now()
    except Exception:
        return datetime.now()
