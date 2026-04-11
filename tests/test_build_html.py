"""Tests for HTML generation (build_html.py)."""
import json
import pytest
from build_html import make_html, _match_slides_to_sections, _slide_html, _load_slides


# ============================================================
# make_html — basic structure
# ============================================================

class TestMakeHtml:

    def test_generates_valid_html(self, sample_translated_txt):
        html = make_html("test123", "Título Teste", "Autor Teste", "https://example.com", sample_translated_txt)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_title(self, sample_translated_txt):
        html = make_html("test123", "Meu Título", "Autor", "https://example.com", sample_translated_txt)
        assert "<title>Meu Título</title>" in html
        assert "<h1>Meu Título</h1>" in html

    def test_contains_subtitle_in_cite(self, sample_translated_txt):
        html = make_html("test123", "T", "Fonte Original", "https://example.com", sample_translated_txt)
        assert "<cite>Fonte Original</cite>" in html

    def test_contains_source_link(self, sample_translated_txt):
        html = make_html("test123", "T", "S", "https://example.com/video", sample_translated_txt)
        assert 'href="https://example.com/video"' in html

    def test_contains_custom_link_text(self, sample_translated_txt):
        html = make_html("test123", "T", "S", "https://x.com", sample_translated_txt, link_text="🐦 Ver no Twitter/X")
        assert "🐦 Ver no Twitter/X" in html

    def test_default_link_text_youtube(self, sample_translated_txt):
        html = make_html("test123", "T", "S", "https://youtube.com", sample_translated_txt)
        assert "Assistir no YouTube" in html

    def test_contains_storage_key(self, sample_translated_txt):
        html = make_html("myVidId", "T", "S", "https://example.com", sample_translated_txt)
        assert 'data-storage-key="reading_myVidId_"' in html

    def test_lang_pt_br(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert 'lang="pt-BR"' in html


# ============================================================
# SEO meta tags
# ============================================================

class TestSeoMetaTags:

    def test_meta_description(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert '<meta name="description"' in html

    def test_og_title(self, sample_translated_txt):
        html = make_html("t", "Meu Título OG", "S", "https://example.com", sample_translated_txt)
        assert '<meta property="og:title" content="Meu Título OG">' in html

    def test_og_type_article(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert '<meta property="og:type" content="article">' in html

    def test_twitter_card(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert '<meta name="twitter:card" content="summary">' in html

    def test_meta_author(self, sample_translated_txt):
        html = make_html("t", "T", "Autor XYZ", "https://example.com", sample_translated_txt)
        assert '<meta name="author" content="Autor XYZ">' in html


# ============================================================
# JSON-LD structured data
# ============================================================

class TestJsonLd:

    def _extract_jsonld(self, html):
        import re
        match = re.search(r'<script type="application/ld\+json">\s*(.+?)\s*</script>', html, re.DOTALL)
        assert match, "JSON-LD not found in HTML"
        return json.loads(match.group(1))

    def test_jsonld_present(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert "application/ld+json" in html

    def test_jsonld_schema_type(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        data = self._extract_jsonld(html)
        assert data["@type"] == "Article"
        assert data["@context"] == "https://schema.org"

    def test_jsonld_headline(self, sample_translated_txt):
        html = make_html("t", "Meu Título", "S", "https://example.com", sample_translated_txt)
        data = self._extract_jsonld(html)
        assert data["headline"] == "Meu Título"

    def test_jsonld_language(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        data = self._extract_jsonld(html)
        assert data["inLanguage"] == "pt-BR"

    def test_jsonld_sections(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        data = self._extract_jsonld(html)
        assert len(data["articleSection"]) >= 2


# ============================================================
# Semantic HTML
# ============================================================

class TestSemanticHtml:

    def test_uses_article_tag(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert "<article" in html
        assert "</article>" in html

    def test_uses_section_tags(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert "<section>" in html
        assert "</section>" in html

    def test_nav_has_aria_label(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert 'aria-label="Índice do artigo"' in html

    def test_external_link_has_noopener(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert 'rel="noopener"' in html


# ============================================================
# Table of contents
# ============================================================

class TestTableOfContents:

    def test_toc_has_sections(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert 'href="#s1"' in html
        assert "INTRODUÇÃO" in html

    def test_section_headings_have_ids(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert 'id="s1"' in html
        assert 'id="s2"' in html


# ============================================================
# Slide injection
# ============================================================

class TestSlideInjection:

    def test_no_slides_no_figures(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt)
        assert "slide-figure" not in html

    def test_slides_injected(self, sample_translated_txt, sample_slides_json):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt, slides_json_path=sample_slides_json)
        assert "slide-figure" in html
        assert "slide-0001.jpg" in html

    def test_slides_have_lazy_loading(self, sample_translated_txt, sample_slides_json):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt, slides_json_path=sample_slides_json)
        assert 'loading="lazy"' in html

    def test_nonexistent_slides_json_ignored(self, sample_translated_txt):
        html = make_html("t", "T", "S", "https://example.com", sample_translated_txt, slides_json_path="/nonexistent.json")
        assert "slide-figure" not in html


# ============================================================
# Slide helper functions
# ============================================================

class TestSlideHelpers:

    def test_match_slides_empty(self):
        assert _match_slides_to_sections([], 5) == {}

    def test_match_slides_zero_sections(self):
        slides = [{"timestamp": 10}]
        assert _match_slides_to_sections(slides, 0) == {}

    def test_match_slides_proportional(self):
        slides = [
            {"timestamp": 0},
            {"timestamp": 50},
            {"timestamp": 100},
        ]
        mapping = _match_slides_to_sections(slides, 3)
        assert 0 in mapping  # first slide → section 0
        assert 2 in mapping  # last slide → last section

    def test_slide_html_structure(self):
        slide = {"timestamp_fmt": "1:30", "path": "img/test/slide-0001.jpg"}
        html = _slide_html(slide)
        assert '<figure class="slide-figure">' in html
        assert 'loading="lazy"' in html
        assert "slide-0001.jpg" in html
        assert "1:30" in html

    def test_load_slides_nonexistent(self):
        assert _load_slides("/nonexistent.json") == []

    def test_load_slides_none(self):
        assert _load_slides(None) == []

    def test_load_slides_valid(self, sample_slides_json):
        slides = _load_slides(sample_slides_json)
        assert len(slides) == 3
        assert slides[0]["timestamp"] == 0
