#!/usr/bin/env python3
"""
Regenerate all EN HTMLs after fixing the slug shadowing bug.
Reads from transcripts/{provider}/{id}_en.txt + EN metadata.
"""
import json
import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))
from build_html import make_html

# Metadata for EN articles — title/subtitle extracted from the generated HTMLs
# so we don't lose the English titles the subagents chose.
EN_ARTICLES = []


def extract_en_metadata(html_path):
    """Extract title and subtitle from an existing EN HTML."""
    with open(html_path) as f:
        html = f.read()
    title = re.search(r'<h1>([^<]+)</h1>', html)
    title = title.group(1).strip() if title else ""
    subtitle = re.search(r'<cite>([^<]+)</cite>', html)
    subtitle = subtitle.group(1).strip() if subtitle else ""
    url = re.search(r'target="_blank"[^>]*>([^<]*)</a>', html)
    link_text = url.group(1).strip() if url else "🎥 Watch on YouTube"
    return title, subtitle, link_text


def main():
    original_dir = os.path.join(PROJECT_DIR, "docs", "posts", "original")
    index_path = os.path.join(PROJECT_DIR, "transcripts", "index.json")
    with open(index_path) as f:
        index = json.load(f)

    count = 0
    for entry in index:
        pt_slug = entry["slug"]
        en_slug = entry.get("slug_en", pt_slug)
        vid_id = entry["video_id"]
        provider = entry["provider"]
        url = entry["url"]

        html_path = os.path.join(original_dir, f"{en_slug}.html")
        txt_path = os.path.join(PROJECT_DIR, "transcripts", provider, f"{vid_id}_en.txt")

        if not os.path.exists(html_path):
            print(f"  SKIP {en_slug} — EN HTML not found")
            continue
        if not os.path.exists(txt_path):
            print(f"  SKIP {en_slug} — EN transcript not found at {txt_path}")
            continue

        en_title, en_subtitle, link_text = extract_en_metadata(html_path)
        if not en_title or not en_subtitle:
            print(f"  SKIP {en_slug} — could not extract EN title/subtitle")
            continue

        if "Watch on YouTube" in link_text or "YouTube" in link_text:
            link_text = "🎥 Watch on YouTube"
        elif "Twitter" in link_text or "X" in link_text:
            link_text = "🐦 View on Twitter/X"
        else:
            link_text = "🎥 Watch on YouTube"

        html = make_html(
            vid_id=vid_id,
            title=en_title,
            subtitle=en_subtitle,
            url=url,
            txt_path=txt_path,
            link_text=link_text,
            lang="original",
            pt_slug=pt_slug,
            en_slug=en_slug,
            provider=provider,
        )
        with open(html_path, "w") as f:
            f.write(html)
        print(f"  OK   {en_slug}")
        count += 1

    print(f"\n{count} HTMLs regenerated")


if __name__ == "__main__":
    main()
