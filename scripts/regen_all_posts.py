#!/usr/bin/env python3
"""
Regenerate every post HTML (PT-BR + EN) from the persisted .txt transcripts.

Used when build_html.py changes (template, reading aids, etc.) and we need to
backfill the new structure into the 70+ existing posts.

Reads:
  transcripts/index.json  → metadata (slug, slug_en, video_id, provider, url, ...)
  transcripts/{provider}/{vid}_pt.txt → PT body
  transcripts/{provider}/{vid}_en.txt → EN body
  transcripts/{provider}/{vid}.references.json (optional) → refs sidebar

Writes:
  docs/posts/pt_br/<slug>.html
  docs/posts/original/<slug_en>.html
"""
import json
import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))
from build_html import make_html


def _extract_meta(html_path):
    """Extract <h1>, <cite>, link text from existing HTML so we don't lose data
    that's only in the file (not in index.json) — applies to both PT and EN."""
    if not os.path.exists(html_path):
        return None
    with open(html_path) as f:
        html = f.read()
    title = re.search(r'<h1>([^<]+)</h1>', html)
    title = title.group(1).strip() if title else ""
    subtitle = re.search(r'<cite>([^<]+)</cite>', html)
    subtitle = subtitle.group(1).strip() if subtitle else ""
    link = re.search(r'target="_blank"[^>]*>([^<]*)</a>', html)
    link_text = link.group(1).strip() if link else ""
    return {"title": title, "subtitle": subtitle, "link_text": link_text}


def main():
    pt_dir   = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")
    en_dir   = os.path.join(PROJECT_DIR, "docs", "posts", "original")
    idx_path = os.path.join(PROJECT_DIR, "transcripts", "index.json")
    with open(idx_path) as f:
        index = json.load(f)

    pt_ok = pt_skip = en_ok = en_skip = 0

    for entry in index:
        vid_id   = entry["video_id"]
        provider = entry["provider"]
        url      = entry["url"]
        pt_slug  = entry.get("slug")
        en_slug  = entry.get("slug_en")

        # ───── PT-BR ─────────────────────────────────────────────────
        if pt_slug:
            pt_html = os.path.join(pt_dir, f"{pt_slug}.html")
            pt_txt  = os.path.join(PROJECT_DIR, "transcripts", provider, f"{vid_id}_pt.txt")
            pt_meta = _extract_meta(pt_html) or {}
            title    = entry.get("title") or pt_meta.get("title", "")
            subtitle = entry.get("subtitle") or pt_meta.get("subtitle", "")
            link_text = pt_meta.get("link_text") or "🎥 Assistir no YouTube"
            if not os.path.exists(pt_txt):
                print(f"  PT skip {pt_slug} — transcript missing")
                pt_skip += 1
            elif not title:
                print(f"  PT skip {pt_slug} — no title")
                pt_skip += 1
            else:
                html = make_html(
                    vid_id=vid_id, title=title, subtitle=subtitle, url=url,
                    txt_path=pt_txt, link_text=link_text,
                    lang="pt_br", slug=pt_slug,
                    pt_slug=pt_slug, en_slug=en_slug,
                    provider=provider,
                )
                os.makedirs(os.path.dirname(pt_html), exist_ok=True)
                with open(pt_html, "w") as f:
                    f.write(html)
                print(f"  PT ok   {pt_slug}")
                pt_ok += 1

        # ───── EN ────────────────────────────────────────────────────
        if en_slug:
            en_html = os.path.join(en_dir, f"{en_slug}.html")
            en_txt  = os.path.join(PROJECT_DIR, "transcripts", provider, f"{vid_id}_en.txt")
            en_meta = _extract_meta(en_html) or {}
            en_title    = entry.get("title_en") or en_meta.get("title", "")
            en_subtitle = entry.get("subtitle_en") or en_meta.get("subtitle", "")
            link_text = en_meta.get("link_text") or "🎥 Watch on YouTube"
            if not os.path.exists(en_txt):
                print(f"  EN skip {en_slug} — transcript missing")
                en_skip += 1
            elif not en_title:
                print(f"  EN skip {en_slug} — no title")
                en_skip += 1
            else:
                html = make_html(
                    vid_id=vid_id, title=en_title, subtitle=en_subtitle, url=url,
                    txt_path=en_txt, link_text=link_text,
                    lang="original", slug=en_slug,
                    pt_slug=pt_slug, en_slug=en_slug,
                    provider=provider,
                )
                os.makedirs(os.path.dirname(en_html), exist_ok=True)
                with open(en_html, "w") as f:
                    f.write(html)
                print(f"  EN ok   {en_slug}")
                en_ok += 1

    print(f"\nPT: {pt_ok} regenerated, {pt_skip} skipped")
    print(f"EN: {en_ok} regenerated, {en_skip} skipped")


if __name__ == "__main__":
    main()
