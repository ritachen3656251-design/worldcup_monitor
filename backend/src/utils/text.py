"""Text processing utilities."""
import re
from bs4 import BeautifulSoup


def truncate_input(text: str, max_chars: int = 1500) -> str:
    """
    Truncate text to max_chars, preserving word boundaries.

    Args:
        text: Input text
        max_chars: Maximum character count (default: 1500)

    Returns:
        Truncated text
    """
    if len(text) <= max_chars:
        return text

    # Truncate and find last space to preserve word boundary
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + "..."


def clean_html(html: str) -> str:
    """
    Clean HTML content by removing tags, ads, and non-Chinese characters.

    Args:
        html: Raw HTML content

    Returns:
        Cleaned text
    """
    # Parse HTML
    soup = BeautifulSoup(html, 'lxml')

    # Remove script and style elements
    for script in soup(["script", "style", "iframe", "noscript"]):
        script.decompose()

    # Remove ads (common class names)
    for ad in soup.find_all(class_=re.compile(r'ad|advertisement|banner|sponsor', re.I)):
        ad.decompose()

    # Get text
    text = soup.get_text()

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    return text


def remove_emojis(text: str) -> str:
    """
    Remove emojis from text.

    Args:
        text: Input text

    Returns:
        Text without emojis
    """
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)


def extract_chinese_text(text: str) -> str:
    """
    Extract Chinese characters and common punctuation from text.

    Args:
        text: Input text

    Returns:
        Text with only Chinese characters and punctuation
    """
    # Keep Chinese characters, numbers, common punctuation, and spaces
    pattern = re.compile(r'[^\u4e00-\u9fff0-9a-zA-Z\s，。！？、；：""''（）《》【】…—·]')
    return pattern.sub('', text)


def clean_text(raw_html: str) -> str:
    """
    Full text cleaning pipeline: HTML → plain text → remove emojis → extract Chinese.

    Args:
        raw_html: Raw HTML content

    Returns:
        Cleaned text
    """
    text = clean_html(raw_html)
    text = remove_emojis(text)
    text = extract_chinese_text(text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text
