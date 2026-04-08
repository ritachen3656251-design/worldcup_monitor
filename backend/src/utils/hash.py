"""Content fingerprinting for deduplication."""
import hashlib


def generate_fingerprint(title: str, content: str, length: int = 100) -> str:
    """
    Generate SHA256 fingerprint for content deduplication.

    Args:
        title: Content title
        content: Content body
        length: Number of characters from content to include (default: 100)

    Returns:
        SHA256 hash as hex string
    """
    # Combine title and first N characters of content
    text = f"{title}{content[:length]}"

    # Generate SHA256 hash
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
