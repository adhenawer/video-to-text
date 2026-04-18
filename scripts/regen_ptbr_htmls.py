#!/usr/bin/env python3
"""
Regenerate PT-BR HTMLs from transcripts/{provider}/{id}_pt.txt.
Mirror of regen_en_htmls.py for the PT side.
"""
import json
import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))
from build_html import make_html


def main():
    ptbr_dir = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")
    index_path = os.path.join(PROJECT_DIR, "transcripts", "index.json")
    with open(index_path) as f:
        index = json.load(f)

    only = set(sys.argv[1:])  # optional video_id filter

    count = 0
    for entry in index:
        vid_id = entry["video_id"]
        if only and vid_id not in only:
            continue

        pt_slug = entry["slug"]
        en_slug = entry.get("slug_en")
        provider = entry["provider"]
        url = entry["url"]
        title = entry["title"]
        subtitle = entry["subtitle"]

        html_path = os.path.join(ptbr_dir, f"{pt_slug}.html")
        txt_path = os.path.join(PROJECT_DIR, "transcripts", provider, f"{vid_id}_pt.txt")

        if not os.path.exists(txt_path):
            print(f"  SKIP {pt_slug} — PT transcript not found at {txt_path}")
            continue

        link_text = "🐦 Ver no Twitter/X" if provider == "twitter" else "🎥 Assistir no YouTube"

        html = make_html(
            vid_id=vid_id,
            title=title,
            subtitle=subtitle,
            url=url,
            txt_path=txt_path,
            link_text=link_text,
            lang="pt_br",
            slug=pt_slug,
            pt_slug=pt_slug,
            en_slug=en_slug,
            provider=provider,
        )
        with open(html_path, "w") as f:
            f.write(html)
        print(f"  OK   {pt_slug}")
        count += 1

    print(f"\n{count} HTMLs regenerated")


if __name__ == "__main__":
    main()
