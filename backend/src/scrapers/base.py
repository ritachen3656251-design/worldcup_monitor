"""Base scraper with unified request function."""
import time
import random
from typing import Optional, Dict, Any
import requests
from requests import Response, RequestException

from src.core.config import get_config
from src.core.logging import get_logger

logger = get_logger(__name__)

# User-Agent pool for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]


def unified_request(
    url: str,
    platform: str,
    method: str = "GET",
    max_retries: int = 3,
    **kwargs
) -> Response:
    """
    Unified HTTP request function with delays, UA rotation, and headers.

    Constitution compliance:
    - Platform-specific delays (虎扑 5s, 懂球帝 3s, B站 2s)
    - User-Agent rotation from pool
    - Browser-mimicking headers
    - Automatic retry with exponential backoff
    - Request/response logging

    Args:
        url: Target URL
        platform: Source platform ('hupu', 'dongqiudi', 'bilibili')
        method: HTTP method (default: GET)
        max_retries: Maximum retry attempts (default: 3)
        **kwargs: Additional requests parameters

    Returns:
        Response object

    Raises:
        RequestException: After max_retries failed attempts
    """
    config = get_config()

    # Get platform-specific delay
    delay = config.scraping.delays.get(platform, 2)

    # Apply delay before request
    time.sleep(delay)

    # Select random User-Agent
    user_agent = random.choice(USER_AGENTS)

    # Build headers
    headers = kwargs.pop("headers", {})
    headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    })

    # Add referer if not present
    if "Referer" not in headers:
        headers["Referer"] = url

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            logger.info(
                "Making request",
                url=url,
                platform=platform,
                method=method,
                attempt=attempt + 1,
            )

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )

            response.raise_for_status()

            logger.info(
                "Request successful",
                url=url,
                platform=platform,
                status_code=response.status_code,
                content_length=len(response.content),
            )

            return response

        except RequestException as e:
            logger.warning(
                "Request failed",
                url=url,
                platform=platform,
                attempt=attempt + 1,
                error=str(e),
            )

            if attempt < max_retries - 1:
                # Exponential backoff: 2^attempt seconds
                backoff = 2 ** attempt
                logger.info(f"Retrying in {backoff} seconds", backoff=backoff)
                time.sleep(backoff)
            else:
                logger.error(
                    "Request failed after max retries",
                    url=url,
                    platform=platform,
                    max_retries=max_retries,
                )
                raise

    # Should never reach here
    raise RequestException(f"Failed to fetch {url} after {max_retries} attempts")
