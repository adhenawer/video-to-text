"""Provider registry — auto-detects video source from URL."""

from .youtube import YouTubeProvider
from .twitter import TwitterProvider

_PROVIDERS = [YouTubeProvider(), TwitterProvider()]


def detect_provider(url: str):
    """Return the first provider that matches the URL, or None."""
    for p in _PROVIDERS:
        if p.detect(url):
            return p
    return None
