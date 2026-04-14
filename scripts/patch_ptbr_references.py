#!/usr/bin/env python3
"""Inject references sidebar into existing PT-BR HTMLs.

The sidebar HTML is produced by build_html._render_references_sidebar(refs, is_ptbr=True)
and placed right before <a class="back-top">.
"""
import json
import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))
from build_html import _render_references_sidebar

PTBR_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")

# Duplicate PT slugs that share a video_id with a canonical PT entry
DUP_TO_CANONICAL = {
    "amit-insights-tecnicos": "obsidian-claude-code-pensamento",
    "ronycoder-arte-comunicar": "entendendo-rony-coder",
    "ronycoder-video": "entendendo-rony-coder",
    "teste-gemma4-pipeline": "de-ides-para-agentes-de-ia-steve-yegge",
    "teste-pipeline-local": "de-ides-para-agentes-de-ia-steve-yegge",
}


def main():
    with open(INDEX_PATH) as f:
        index = json.load(f)
    by_slug = {e["slug"]: e for e in index}

    count = 0
    for fname in sorted(os.listdir(PTBR_DIR)):
        if not fname.endswith(".html"):
            continue
        slug = fname.replace(".html", "")
        canonical = DUP_TO_CANONICAL.get(slug, slug)
        entry = by_slug.get(canonical)
        if not entry:
            print(f"  SKIP {slug} — no manifest entry")
            continue

        refs_path = os.path.join(
            PROJECT_DIR, "transcripts", entry["provider"],
            f"{entry['video_id']}.references.json"
        )
        if not os.path.exists(refs_path):
            print(f"  SKIP {slug} — no references JSON")
            continue

        with open(refs_path) as f:
            refs = json.load(f)

        sidebar_html = _render_references_sidebar(refs, is_ptbr=True)

        html_path = os.path.join(PTBR_DIR, fname)
        with open(html_path) as f:
            html = f.read()

        # Remove any existing sidebar first (idempotent)
        html = re.sub(
            r'<aside class="references-sidebar".*?</aside>\s*',
            '',
            html,
            flags=re.DOTALL
        )

        # Insert new sidebar right before <a class="back-top" or <a href="#" class="back-top"
        insertion = sidebar_html + '\n'
        if '<a href="#" class="back-top"' in html:
            html = html.replace(
                '<a href="#" class="back-top"',
                insertion + '<a href="#" class="back-top"',
                1
            )
        elif '<a class="back-top"' in html:
            html = html.replace(
                '<a class="back-top"',
                insertion + '<a class="back-top"',
                1
            )
        else:
            print(f"  SKIP {slug} — no back-top marker")
            continue

        with open(html_path, "w") as f:
            f.write(html)
        print(f"  OK   {slug}  ({entry.get('references', {}).get('total', 0)} refs)")
        count += 1

    print(f"\n{count} PT-BR HTMLs patched with references sidebar")


if __name__ == "__main__":
    main()
