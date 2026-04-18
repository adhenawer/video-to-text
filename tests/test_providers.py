"""Tests for provider detection, URL parsing and metadata."""
import pytest
from providers import detect_provider
from providers.youtube import YouTubeProvider, _format_timestamp, _seg_to_dict
from providers.twitter import TwitterProvider, _format_timestamp as tw_format_ts


# ============================================================
# YouTube Provider
# ============================================================

class TestYouTubeProvider:

    def setup_method(self):
        self.provider = YouTubeProvider()

    # --- detect() ---

    def test_detect_standard_url(self):
        assert self.provider.detect("https://www.youtube.com/watch?v=abc123def45")

    def test_detect_short_url(self):
        assert self.provider.detect("https://youtu.be/abc123def45")

    def test_detect_shorts_url(self):
        assert self.provider.detect("https://youtube.com/shorts/abc123def45")

    def test_detect_rejects_twitter(self):
        assert not self.provider.detect("https://x.com/user/status/123")

    def test_detect_rejects_random_url(self):
        assert not self.provider.detect("https://vimeo.com/12345")

    # --- extract_id() ---

    def test_extract_id_standard(self):
        assert self.provider.extract_id("https://www.youtube.com/watch?v=abc123def45") == "abc123def45"

    def test_extract_id_short_url(self):
        assert self.provider.extract_id("https://youtu.be/abc123def45") == "abc123def45"

    def test_extract_id_with_params(self):
        assert self.provider.extract_id("https://www.youtube.com/watch?v=abc123def45&t=120") == "abc123def45"

    def test_extract_id_shorts(self):
        assert self.provider.extract_id("https://youtube.com/shorts/abc123def45") == "abc123def45"

    def test_extract_id_embed(self):
        assert self.provider.extract_id("https://youtube.com/embed/abc123def45") == "abc123def45"

    def test_extract_id_live(self):
        assert self.provider.extract_id("https://youtube.com/live/abc123def45") == "abc123def45"

    def test_extract_id_raw_id(self):
        assert self.provider.extract_id("abc123def45") == "abc123def45"

    def test_extract_id_with_whitespace(self):
        assert self.provider.extract_id("  abc123def45  ") == "abc123def45"

    # --- metadata ---

    def test_name(self):
        assert self.provider.name == "youtube"

    def test_display_name(self):
        assert self.provider.display_name == "YouTube"

    def test_link_text(self):
        assert "YouTube" in self.provider.link_text

    # --- build_video_url() ---

    def test_build_video_url_short_form(self):
        url = self.provider.build_video_url("https://youtu.be/abc123def45", 779)
        assert url == "https://youtu.be/abc123def45?t=779"

    def test_build_video_url_watch_form(self):
        url = self.provider.build_video_url("https://www.youtube.com/watch?v=abc123def45", 779)
        assert url == "https://www.youtube.com/watch?v=abc123def45&t=779"

    def test_build_video_url_replaces_existing_t(self):
        url = self.provider.build_video_url("https://www.youtube.com/watch?v=abc123def45&t=120", 779)
        assert "t=779" in url
        assert "t=120" not in url

    def test_build_video_url_zero_seconds(self):
        url = self.provider.build_video_url("https://youtu.be/abc", 0)
        assert url == "https://youtu.be/abc?t=0"


# ============================================================
# Twitter Provider
# ============================================================

class TestTwitterProvider:

    def setup_method(self):
        self.provider = TwitterProvider()

    # --- detect() ---

    def test_detect_x_url(self):
        assert self.provider.detect("https://x.com/user/status/123456789")

    def test_detect_twitter_url(self):
        assert self.provider.detect("https://twitter.com/user/status/123456789")

    def test_detect_rejects_youtube(self):
        assert not self.provider.detect("https://youtube.com/watch?v=abc123")

    def test_detect_rejects_x_profile(self):
        assert not self.provider.detect("https://x.com/user")

    def test_detect_rejects_x_without_status(self):
        assert not self.provider.detect("https://x.com/user/likes")

    # --- extract_id() ---

    def test_extract_id_x(self):
        assert self.provider.extract_id("https://x.com/user/status/2042172428127002906") == "2042172428127002906"

    def test_extract_id_twitter(self):
        assert self.provider.extract_id("https://twitter.com/user/status/123456") == "123456"

    def test_extract_id_with_params(self):
        assert self.provider.extract_id("https://x.com/user/status/123456?s=20") == "123456"

    def test_extract_id_invalid_raises(self):
        with pytest.raises(ValueError):
            self.provider.extract_id("https://x.com/user/likes")

    # --- metadata ---

    def test_name(self):
        assert self.provider.name == "twitter"

    def test_display_name(self):
        assert self.provider.display_name == "Twitter/X"

    def test_link_text(self):
        assert "Twitter" in self.provider.link_text

    # --- build_video_url() ---

    def test_build_video_url_returns_none(self):
        # Twitter/X has no documented timestamp deep-link support
        assert self.provider.build_video_url("https://x.com/i/status/123", 779) is None


# ============================================================
# Provider Registry
# ============================================================

class TestProviderRegistry:

    def test_detect_youtube(self):
        p = detect_provider("https://youtube.com/watch?v=abc123def45")
        assert p is not None
        assert p.name == "youtube"

    def test_detect_twitter(self):
        p = detect_provider("https://x.com/user/status/123456")
        assert p is not None
        assert p.name == "twitter"

    def test_detect_unknown_returns_none(self):
        assert detect_provider("https://vimeo.com/12345") is None

    def test_detect_empty_string(self):
        assert detect_provider("") is None

    def test_detect_random_text(self):
        assert detect_provider("not a url at all") is None


# ============================================================
# Timestamp formatting
# ============================================================

class TestFormatTimestamp:

    def test_zero(self):
        assert _format_timestamp(0) == "0:00"

    def test_seconds(self):
        assert _format_timestamp(45) == "0:45"

    def test_minutes(self):
        assert _format_timestamp(125) == "2:05"

    def test_hours(self):
        assert _format_timestamp(3661) == "1:01:01"

    def test_float(self):
        assert _format_timestamp(90.7) == "1:30"

    def test_twitter_format_matches(self):
        assert tw_format_ts(125) == "2:05"
        assert tw_format_ts(3661) == "1:01:01"


# ============================================================
# Segment conversion
# ============================================================

class TestSegToDict:

    def test_dict_passthrough(self):
        seg = {"text": "hello", "start": 1.0, "duration": 2.0}
        assert _seg_to_dict(seg) == seg

    def test_object_conversion(self):
        class FakeSeg:
            text = "hello"
            start = 1.0
            duration = 2.0
        result = _seg_to_dict(FakeSeg())
        assert result == {"text": "hello", "start": 1.0, "duration": 2.0}
