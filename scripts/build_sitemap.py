#!/usr/bin/env python3
"""
Generate docs/sitemap.xml with hreflang alternates for each article pair.
Also updates docs/llms.txt with both-language entries.
"""
import json
import os
from datetime import date

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")
SITEMAP_PATH = os.path.join(PROJECT_DIR, "docs", "sitemap.xml")
LLMS_PATH = os.path.join(PROJECT_DIR, "docs", "llms.txt")

BASE = "https://adhenawer.net"
TODAY = str(date.today())


def build_sitemap():
    with open(INDEX_PATH) as f:
        index = json.load(f)

    urls = []

    # Root (PT) + EN index
    urls.append({
        "loc": f"{BASE}/",
        "lastmod": TODAY,
        "changefreq": "weekly",
        "priority": "1.0",
        "alternates": {
            "pt-BR": f"{BASE}/",
            "en": f"{BASE}/en/",
            "x-default": f"{BASE}/",
        },
    })
    urls.append({
        "loc": f"{BASE}/en/",
        "lastmod": TODAY,
        "changefreq": "weekly",
        "priority": "0.9",
        "alternates": {
            "pt-BR": f"{BASE}/",
            "en": f"{BASE}/en/",
            "x-default": f"{BASE}/",
        },
    })

    for entry in index:
        pt_slug = entry["slug"]
        en_slug = entry.get("slug_en")
        pt_url = f"{BASE}/posts/pt_br/{pt_slug}.html"
        en_url = f"{BASE}/posts/original/{en_slug}.html" if en_slug else None

        alts = {"pt-BR": pt_url, "x-default": pt_url}
        if en_url:
            alts["en"] = en_url

        urls.append({
            "loc": pt_url,
            "lastmod": TODAY,
            "changefreq": "monthly",
            "priority": "0.8",
            "alternates": alts,
        })
        if en_url:
            urls.append({
                "loc": en_url,
                "lastmod": TODAY,
                "changefreq": "monthly",
                "priority": "0.8",
                "alternates": alts,
            })

    # Build XML
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for u in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{u['loc']}</loc>")
        lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        lines.append(f"    <priority>{u['priority']}</priority>")
        for hreflang, href in u["alternates"].items():
            lines.append(
                f'    <xhtml:link rel="alternate" hreflang="{hreflang}" href="{href}"/>'
            )
        lines.append("  </url>")
    lines.append("</urlset>")

    with open(SITEMAP_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"OK {SITEMAP_PATH} ({len(urls)} URLs)")


def build_llms_txt():
    with open(INDEX_PATH) as f:
        index = json.load(f)

    lines = [
        "# Leituras — Translated Podcasts & Videos / Podcasts & Vídeos Traduzidos",
        "",
        "> Bilingual site (PT-BR + English) with articles from podcasts and videos about AI, tech and finance.",
        "> Each article is a full transcript organized into thematic sections.",
        "> Source: YouTube and Twitter/X videos.",
        "",
        "## Articles — Português (PT-BR)",
        "",
    ]

    for entry in index:
        pt_slug = entry["slug"]
        title = entry.get("title", "")
        subtitle = entry.get("subtitle", "")
        lines.append(f"- [{title}]({BASE}/posts/pt_br/{pt_slug}.html)")
        lines.append(f"  Fonte: {subtitle}")
        lines.append("")

    lines.append("## Articles — English")
    lines.append("")

    for entry in index:
        en_slug = entry.get("slug_en")
        if not en_slug:
            continue
        en_html = os.path.join(PROJECT_DIR, "docs", "posts", "original", f"{en_slug}.html")
        if not os.path.exists(en_html):
            continue
        # Get EN title/subtitle
        import re
        with open(en_html) as f:
            html = f.read()
        en_title = re.search(r"<h1>([^<]+)</h1>", html)
        en_title = en_title.group(1).strip() if en_title else ""
        en_subtitle = re.search(r"<cite>([^<]+)</cite>", html)
        en_subtitle = en_subtitle.group(1).strip() if en_subtitle else ""
        lines.append(f"- [{en_title}]({BASE}/posts/original/{en_slug}.html)")
        lines.append(f"  Source: {en_subtitle}")
        lines.append("")

    with open(LLMS_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"OK {LLMS_PATH}")


if __name__ == "__main__":
    build_sitemap()
    build_llms_txt()
