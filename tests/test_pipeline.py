"""Tests for pipeline argument parsing and provider detection."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from providers import detect_provider


class TestPipelineProviderDetection:
    """Test that the pipeline correctly routes URLs to providers."""

    def test_youtube_standard(self):
        p = detect_provider("https://www.youtube.com/watch?v=abc123def45")
        assert p.name == "youtube"

    def test_youtube_short(self):
        p = detect_provider("https://youtu.be/abc123def45")
        assert p.name == "youtube"

    def test_twitter_x(self):
        p = detect_provider("https://x.com/user/status/2042172428127002906")
        assert p.name == "twitter"

    def test_twitter_legacy(self):
        p = detect_provider("https://twitter.com/user/status/123456789")
        assert p.name == "twitter"

    def test_unknown_url(self):
        assert detect_provider("https://vimeo.com/12345") is None

    def test_empty_url(self):
        assert detect_provider("") is None


class TestProviderInterface:
    """Test that all providers implement the required interface."""

    @pytest.fixture(params=["youtube", "twitter"])
    def provider(self, request):
        urls = {
            "youtube": "https://youtube.com/watch?v=abc123def45",
            "twitter": "https://x.com/user/status/123456789",
        }
        p = detect_provider(urls[request.param])
        assert p is not None
        return p

    def test_has_name(self, provider):
        assert isinstance(provider.name, str)
        assert len(provider.name) > 0

    def test_has_display_name(self, provider):
        assert isinstance(provider.display_name, str)
        assert len(provider.display_name) > 0

    def test_has_link_text(self, provider):
        assert isinstance(provider.link_text, str)
        assert len(provider.link_text) > 0

    def test_has_detect_method(self, provider):
        assert callable(getattr(provider, "detect", None))

    def test_has_extract_id_method(self, provider):
        assert callable(getattr(provider, "extract_id", None))

    def test_has_fetch_transcript_method(self, provider):
        assert callable(getattr(provider, "fetch_transcript", None))
