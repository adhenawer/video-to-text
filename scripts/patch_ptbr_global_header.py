#!/usr/bin/env python3
"""
Patch existing PT-BR HTMLs to:
- Replace inline lang-bar with site-header (fixed top)
- Add hreflang alternate links in <head>
- Include js/lang.js script
"""
import json
import os
import re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTBR_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")


def build_mapping():
    """slug -> {pt_slug, en_slug}. For dups, use canonical EN."""
    with open(INDEX_PATH) as f:
        index = json.load(f)
    # Index has the official pt_slug + slug_en
    by_pt = {}
    for entry in index:
        by_pt[entry["slug"]] = {
            "pt_slug": entry["slug"],
            "en_slug": entry.get("slug_en"),
        }

    # Duplicate slugs (PT-only) — map to their canonical EN counterpart
    # We already ran fix_lang_links.py which updated these; here we extract the EN slug
    # by reading the current PT-BR HTML's existing EN link.
    dups = {
        "amit-insights-tecnicos": "obsidian-claude-code-pensamento",
        "ronycoder-arte-comunicar": "entendendo-rony-coder",
        "ronycoder-video": "entendendo-rony-coder",
        "teste-gemma4-pipeline": "de-ides-para-agentes-de-ia-steve-yegge",
        "teste-pipeline-local": "de-ides-para-agentes-de-ia-steve-yegge",
    }
    for pt_slug, canonical_pt in dups.items():
        entry = by_pt.get(canonical_pt)
        if entry:
            by_pt[pt_slug] = {
                "pt_slug": pt_slug,
                "en_slug": entry["en_slug"],
            }

    # EN-less slugs (Chinese, Dario): en_slug is None
    by_pt.setdefault("trading-com-order-flow-mercado-global-ao-chines", {
        "pt_slug": "trading-com-order-flow-mercado-global-ao-chines",
        "en_slug": None,
    })
    by_pt.setdefault("dario-amodei-scaling-rl-agi-futuro-anthropic", {
        "pt_slug": "dario-amodei-scaling-rl-agi-futuro-anthropic",
        "en_slug": None,
    })
    return by_pt


def patch_html(path, pt_slug, en_slug):
    with open(path) as f:
        html = f.read()

    # 1. Ensure hreflang alternate links are in <head>
    pt_href = f"../pt_br/{pt_slug}.html"
    en_href = f"../original/{en_slug}.html" if en_slug else None

    hreflang_block = f'<link rel="alternate" hreflang="pt-BR" href="{pt_href}">\n'
    if en_href:
        hreflang_block += f'<link rel="alternate" hreflang="en" href="{en_href}">\n'
    hreflang_block += f'<link rel="alternate" hreflang="x-default" href="{pt_href}">\n'

    if "<link rel=\"alternate\" hreflang" not in html:
        html = html.replace(
            '<link rel="stylesheet"',
            hreflang_block + '<link rel="stylesheet"',
            1
        )

    # 2. Insert site-header right after <body ...>
    if '<header class="site-header">' not in html:
        site_header = (
            '<header class="site-header">\n'
            '  <a class="site-brand" href="../../index.html">🎙 Leituras</a>\n'
            '  <div class="lang-bar">\n'
            '    <button class="lang-btn" data-lang="pt-BR" aria-label="Português">🇧🇷 PT</button>\n'
            '    <button class="lang-btn" data-lang="en" aria-label="English">🇺🇸 EN</button>\n'
            '  </div>\n'
            '</header>\n'
        )
        html = re.sub(
            r'(<body[^>]*>)',
            r'\1\n' + site_header,
            html,
            count=1
        )

    # 3. Remove old inline lang-bar inside article
    html = re.sub(
        r'\s*<div class="lang-bar">.*?</div>\s*\n',
        '\n',
        html,
        count=1,
        flags=re.DOTALL
    )

    # 4. Include js/lang.js before </body>
    if 'js/lang.js' not in html:
        html = html.replace(
            '</body>',
            '<script src="../../js/lang.js"></script>\n</body>',
            1
        )

    with open(path, "w") as f:
        f.write(html)


def main():
    mapping = build_mapping()
    count = 0
    for fname in sorted(os.listdir(PTBR_DIR)):
        if not fname.endswith(".html"):
            continue
        slug = fname.replace(".html", "")
        info = mapping.get(slug)
        if not info:
            print(f"  SKIP {slug} — no mapping")
            continue
        path = os.path.join(PTBR_DIR, fname)
        patch_html(path, info["pt_slug"], info["en_slug"])
        en_label = info["en_slug"] or "(no EN)"
        print(f"  OK   {slug}  →  EN: {en_label}")
        count += 1
    print(f"\n{count} PT-BR HTMLs patched")


if __name__ == "__main__":
    main()
