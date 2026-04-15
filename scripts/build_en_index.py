#!/usr/bin/env python3
"""
Build docs/en/index.html — English landing page.
Mirrors the PT-BR index but links to /posts/original/{en_slug}.html
and uses English titles/subtitles extracted from each EN HTML.
"""
import json
import os
import re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "original")
EN_DIR = os.path.join(PROJECT_DIR, "docs", "en")
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")


def extract_en_metadata(en_html_path):
    with open(en_html_path) as f:
        html = f.read()
    title = re.search(r"<h1>([^<]+)</h1>", html)
    title = title.group(1).strip() if title else ""
    subtitle = re.search(r"<cite>([^<]+)</cite>", html)
    subtitle = subtitle.group(1).strip() if subtitle else ""
    description = re.search(r'<meta name="description" content="([^"]+)"', html)
    description = description.group(1).strip() if description else ""
    # Count sections by h2 count
    sections = len(re.findall(r"<h2\s", html))
    return {
        "title": title,
        "subtitle": subtitle,
        "description": description,
        "sections": sections,
    }


def main():
    os.makedirs(EN_DIR, exist_ok=True)

    with open(INDEX_PATH) as f:
        index = json.load(f)

    cards = []
    for entry in index:
        en_slug = entry.get("slug_en")
        if not en_slug:
            continue
        en_html = os.path.join(ORIGINAL_DIR, f"{en_slug}.html")
        if not os.path.exists(en_html):
            continue
        meta = extract_en_metadata(en_html)
        source_label = "YouTube" if entry["provider"] == "youtube" else "Twitter/X"
        card = f'''  <a class="card" href="../posts/original/{en_slug}.html">
    <div class="card-top"><h2>{meta["title"]}</h2></div>
    <div class="meta"><span>{source_label}</span><span>{meta["subtitle"]}</span><span>{meta["sections"]} sections</span></div>
    <div class="desc">{meta["description"]}</div>
    <div class="progress-info" id="p-{entry["video_id"][:8]}"></div>
  </a>'''
        cards.append(card)

    cards_html = "\n\n".join(cards)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Readings — Translated Podcasts &amp; Videos</title>
<meta name="description" content="Podcasts and videos on AI, tech and finance transcribed and organized as articles. Both original-language and Brazilian Portuguese versions.">
<meta name="author" content="adhenawer">
<meta property="og:type" content="website">
<meta property="og:title" content="Readings — Translated Podcasts &amp; Videos">
<meta property="og:description" content="Podcasts and videos on AI, tech and finance transcribed and organized as articles.">
<meta property="og:locale" content="en_US">
<meta property="og:site_name" content="Readings">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Readings — Translated Podcasts &amp; Videos">
<meta name="twitter:description" content="Podcasts and videos on AI, tech and finance as articles.">
<link rel="alternate" hreflang="pt-BR" href="/">
<link rel="alternate" hreflang="en" href="/en/">
<link rel="alternate" hreflang="x-default" href="/">
<link rel="stylesheet" href="../css/style.css">
</head>
<body class="page-index" data-auto-redirect="true">
<header class="site-header">
  <a class="site-brand" href="/en/">Readings</a>
  <div class="lang-bar">
    <button class="lang-btn" data-lang="pt-BR" aria-label="Português">PT</button>
    <button class="lang-btn" data-lang="en" aria-label="English">EN</button>
  </div>
</header>
<div class="container">
  <header>
    <h1>Readings <a href="https://github.com/adhenawer/video-to-text" target="_blank" rel="noopener" class="github-link" title="View on GitHub"><svg height="24" width="24" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg></a></h1>
    <p>Podcasts and videos transcribed and organized as readable articles</p>
    <p class="meta" style="margin-top:8px"><a href="../blog/en/">Blog</a> — notes about the project · <a href="../moc.html">Map</a> — graph of articles</p>
  </header>

  <div class="section-title">Articles</div>

{cards_html}
</div>
<script src="../js/lang.js"></script>
</body>
</html>'''

    out_path = os.path.join(EN_DIR, "index.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"OK {out_path} ({len(cards)} cards, {len(html):,} bytes)")


if __name__ == "__main__":
    main()
