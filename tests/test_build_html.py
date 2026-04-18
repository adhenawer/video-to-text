"""Tests for HTML generation (build_html.py)."""
import json
import pytest
from build_html import (
    make_html, _match_slides_to_sections, _slide_html, _load_slides,
    _parse_section_heading, _timestamp_to_seconds,
)


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
# Section heading timestamp parsing
# ============================================================

class TestParseSectionHeading:

    def test_with_mmss_timestamp(self):
        title, secs = _parse_section_heading("[12:34] INTRODUÇÃO")
        assert title == "INTRODUÇÃO"
        assert secs == 754  # 12*60 + 34

    def test_with_hhmmss_timestamp(self):
        title, secs = _parse_section_heading("[1:02:03] CAPÍTULO LONGO")
        assert title == "CAPÍTULO LONGO"
        assert secs == 3723  # 3600 + 120 + 3

    def test_without_timestamp(self):
        title, secs = _parse_section_heading("INTRODUÇÃO")
        assert title == "INTRODUÇÃO"
        assert secs is None

    def test_zero_timestamp(self):
        title, secs = _parse_section_heading("[0:00] ABERTURA")
        assert title == "ABERTURA"
        assert secs == 0

    def test_extra_whitespace(self):
        title, secs = _parse_section_heading("[5:00]   TÍTULO COM ESPAÇOS")
        assert title == "TÍTULO COM ESPAÇOS"
        assert secs == 300


class TestTimestampToSeconds:

    def test_mmss(self):
        assert _timestamp_to_seconds("12:34") == 754

    def test_hhmmss(self):
        assert _timestamp_to_seconds("1:02:03") == 3723

    def test_zero(self):
        assert _timestamp_to_seconds("0:00") == 0

    def test_single_digit_minutes(self):
        assert _timestamp_to_seconds("5:30") == 330


# ============================================================
# Section timestamp rendering in HTML
# ============================================================

class TestSectionTimestampRendering:

    @pytest.fixture
    def timestamped_txt(self, tmp_path):
        content = """================================================================================
[0:00] INTRODUÇÃO

Primeiro parágrafo da introdução.

================================================================================
[12:34] DESENVOLVIMENTO

Segundo bloco com mais conteúdo do tema central.

================================================================================
[45:00] CONCLUSÃO

Encerramento do artigo com pontos finais.
"""
        path = tmp_path / "ts.txt"
        path.write_text(content)
        return str(path)

    def test_youtube_emits_timestamp_link(self, timestamped_txt):
        html = make_html("vid", "T", "S", "https://youtu.be/abc123", timestamped_txt)
        # Section heading should have a clickable timestamp link to the video
        assert 'class="ts-link"' in html
        assert 'href="https://youtu.be/abc123?t=754"' in html
        assert '>12:34<' in html

    def test_youtube_section_title_intact(self, timestamped_txt):
        html = make_html("vid", "T", "S", "https://youtu.be/abc123", timestamped_txt)
        assert ">DESENVOLVIMENTO" in html  # title preserved without [12:34] prefix
        assert "[12:34]" not in html  # raw bracket form stripped from h2

    def test_twitter_emits_plain_timestamp_no_link(self, timestamped_txt):
        html = make_html("vid", "T", "S", "https://x.com/i/status/123", timestamped_txt)
        assert 'class="ts-mark"' in html
        assert '>12:34<' in html
        # Twitter has no time deep-link, so no ts-link with ?t=
        assert '?t=' not in html

    def test_no_timestamp_no_extras(self, sample_translated_txt):
        # Backward compat: posts without [mm:ss] should render normally, no ts elements
        html = make_html("vid", "T", "S", "https://youtu.be/abc", sample_translated_txt)
        assert 'class="ts-link"' not in html
        assert 'class="ts-mark"' not in html


# ============================================================
# hreflang alternates
# ============================================================

class TestHreflangAlternates:

    def test_ptbr_with_no_en_omits_en_alternate(self, sample_translated_txt):
        html = make_html("vid", "T", "S", "https://example.com", sample_translated_txt,
                         lang="pt_br", slug="meu-slug", pt_slug="meu-slug", en_slug=None)
        assert 'hreflang="en"' not in html
        assert 'hreflang="pt-BR"' in html

    def test_ptbr_with_en_emits_both_alternates(self, sample_translated_txt):
        html = make_html("vid", "T", "S", "https://example.com", sample_translated_txt,
                         lang="pt_br", slug="meu-slug", pt_slug="meu-slug", en_slug="my-slug")
        assert 'hreflang="pt-BR"' in html
        assert 'href="../pt_br/meu-slug.html"' in html
        assert 'hreflang="en"' in html
        assert 'href="../original/my-slug.html"' in html

    def test_en_with_no_ptbr_omits_ptbr_alternate(self, sample_translated_txt):
        html = make_html("vid", "T", "S", "https://example.com", sample_translated_txt,
                         lang="original", slug="my-slug", pt_slug=None, en_slug="my-slug")
        assert 'hreflang="pt-BR"' not in html
        assert 'hreflang="en"' in html


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
