"""Tests for slide extraction (extract_slides.py)."""
import json
import os
import pytest
from extract_slides import _format_ts, build_slides_json


# ============================================================
# Timestamp formatting
# ============================================================

class TestFormatTs:

    def test_zero(self):
        assert _format_ts(0) == "0:00"

    def test_seconds(self):
        assert _format_ts(45) == "0:45"

    def test_minutes(self):
        assert _format_ts(125) == "2:05"

    def test_exact_minute(self):
        assert _format_ts(60) == "1:00"

    def test_large_value(self):
        assert _format_ts(3599) == "59:59"


# ============================================================
# build_slides_json
# ============================================================

class TestBuildSlidesJson:

    def test_creates_json_file(self, tmp_dir):
        slides = [
            {"timestamp": 10, "filename": "slide-0001.jpg"},
            {"timestamp": 60, "filename": "slide-0002.jpg"},
        ]
        segments = [
            {"start": 8, "end": 12, "text": "First segment"},
            {"start": 55, "end": 65, "text": "Second segment"},
        ]
        output = str(tmp_dir / "slides.json")
        result = build_slides_json(slides, segments, "test-slug", output)

        assert os.path.exists(output)
        assert len(result) == 2

    def test_nearest_text_matching(self, tmp_dir):
        slides = [{"timestamp": 10, "filename": "slide-0001.jpg"}]
        segments = [
            {"start": 5, "end": 8, "text": "Far away"},
            {"start": 9, "end": 12, "text": "Very close"},
            {"start": 50, "end": 55, "text": "Too far"},
        ]
        output = str(tmp_dir / "slides.json")
        result = build_slides_json(slides, segments, "slug", output)

        assert result[0]["nearest_text"] == "Very close"

    def test_path_includes_slug(self, tmp_dir):
        slides = [{"timestamp": 0, "filename": "slide-0001.jpg"}]
        segments = [{"start": 0, "end": 5, "text": "hello"}]
        output = str(tmp_dir / "slides.json")
        result = build_slides_json(slides, segments, "my-slug", output)

        assert result[0]["path"] == "img/my-slug/slide-0001.jpg"

    def test_timestamp_fmt(self, tmp_dir):
        slides = [{"timestamp": 125, "filename": "slide-0001.jpg"}]
        segments = [{"start": 120, "end": 130, "text": "text"}]
        output = str(tmp_dir / "slides.json")
        result = build_slides_json(slides, segments, "s", output)

        assert result[0]["timestamp_fmt"] == "2:05"

    def test_empty_slides(self, tmp_dir):
        output = str(tmp_dir / "slides.json")
        result = build_slides_json([], [], "s", output)

        assert result == []
        with open(output) as f:
            assert json.load(f) == []

    def test_json_file_content(self, tmp_dir):
        slides = [{"timestamp": 30, "filename": "slide-0001.jpg"}]
        segments = [{"start": 28, "end": 35, "text": "some text"}]
        output = str(tmp_dir / "slides.json")
        build_slides_json(slides, segments, "slug", output)

        with open(output) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["timestamp"] == 30
        assert data[0]["nearest_text"] == "some text"
