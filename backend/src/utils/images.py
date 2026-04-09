"""Image handling utilities for card display."""
import os
import hashlib
from typing import Optional, List
from pathlib import Path

from src.core.config import get_config
from src.core.logging import get_logger

logger = get_logger(__name__)

# Theme image library mapping categories to default images
THEME_IMAGES = {
    "转会传闻": "/theme-images/transfer.jpg",
    "球队动态": "/theme-images/team.jpg",
    "赛程赛制": "/theme-images/schedule.jpg",
    "球迷讨论": "/theme-images/fans.jpg",
}


def proxy_image(image_url: str) -> Optional[str]:
    """
    Cache/proxy an original image URL.

    In MVP, we just validate and return the original URL.
    Future: download and cache locally for reliability.

    Args:
        image_url: Original image URL

    Returns:
        Proxied/cached image URL, or None if invalid
    """
    if not image_url:
        return None

    # Basic URL validation
    if not image_url.startswith(("http://", "https://")):
        return None

    # In MVP, return original URL directly
    # Future: download, resize, and cache locally
    return image_url


def match_theme_image(category: str) -> Optional[str]:
    """
    Match a category to a theme library image.

    Args:
        category: Card category (转会传闻, 球队动态, etc.)

    Returns:
        Theme image URL path, or None if no match
    """
    return THEME_IMAGES.get(category)


def select_card_image(
    original_urls: List[str],
    category: str,
) -> Optional[str]:
    """
    Select the best image for a card.

    Strategy: original image > theme image > null

    Args:
        original_urls: List of image URLs from source content
        category: Card category for theme fallback

    Returns:
        Selected image URL, or None
    """
    # Try original images first
    for url in original_urls:
        proxied = proxy_image(url)
        if proxied:
            return proxied

    # Fallback to theme image
    theme = match_theme_image(category)
    if theme:
        return theme

    # No image available
    return None
