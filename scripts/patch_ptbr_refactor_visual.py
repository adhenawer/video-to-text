#!/usr/bin/env python3
"""
Patch PT-BR HTMLs for the visual refactor:
- Remove theme-bar block
- Remove back-top link
- Replace emoji brand (🎙 Leituras → Leituras)
- Replace emoji TOC heading (📑 Índice → Conteúdo)
- Replace emoji resume banner text
- Replace lang buttons (🇧🇷 PT → PT, 🇺🇸 EN → EN)
- Simplify back-home link (← Voltar ao índice → ← Voltar)
- Re-render references sidebar without emojis using current build_html
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

DUP_TO_CANONICAL = {
    "amit-insights-tecnicos": "obsidian-claude-code-pensamento",
    "ronycoder-arte-comunicar": "entendendo-rony-coder",
    "ronycoder-video": "entendendo-rony-coder",
    "teste-gemma4-pipeline": "de-ides-para-agentes-de-ia-steve-yegge",
    "teste-pipeline-local": "de-ides-para-agentes-de-ia-steve-yegge",
}


def patch(html, slug, refs):
    # Remove theme-bar entirely
    html = re.sub(
        r'\s*<div class="theme-bar">.*?</div>\s*',
        '\n  ',
        html,
        count=1,
        flags=re.DOTALL
    )

    # Remove back-top link
    html = re.sub(r'\s*<a href="#" class="back-top"[^>]*>.*?</a>\s*', '\n', html, count=1)

    # Simplify site-brand (remove 🎙 emoji)
    html = re.sub(
        r'<a class="site-brand" href="([^"]+)">\s*🎙\s*Leituras\s*</a>',
        r'<a class="site-brand" href="\1">Leituras</a>',
        html
    )

    # Simplify lang buttons (remove flag emojis)
    html = re.sub(r'>🇧🇷\s*PT</button>', '>PT</button>', html)
    html = re.sub(r'>🇺🇸\s*EN</button>', '>EN</button>', html)

    # TOC heading (remove 📑 emoji)
    html = html.replace('<h3>📑 Índice</h3>', '<h3>Conteúdo</h3>')

    # Resume banner text (remove 📖 emoji)
    html = html.replace(
        '📖 Continuar de onde parou',
        'Continuar de onde parou'
    )

    # Back-home link simplify
    html = html.replace(
        'class="back-home">← Voltar ao índice</a>',
        'class="back-home">← Voltar</a>'
    )

    # Re-render references sidebar (without emojis — current build_html version)
    if refs:
        new_sidebar = _render_references_sidebar(refs, is_ptbr=True)
        html = re.sub(
            r'<aside class="references-sidebar".*?</aside>\s*',
            new_sidebar + '\n',
            html,
            count=1,
            flags=re.DOTALL
        )

    return html


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
        refs = None
        if entry:
            refs_path = os.path.join(
                PROJECT_DIR, "transcripts", entry["provider"],
                f"{entry['video_id']}.references.json"
            )
            if os.path.exists(refs_path):
                with open(refs_path) as f:
                    refs = json.load(f)

        path = os.path.join(PTBR_DIR, fname)
        with open(path) as f:
            html = f.read()

        new_html = patch(html, slug, refs)

        with open(path, "w") as f:
            f.write(new_html)

        count += 1
        print(f"  OK {slug}")

    print(f"\n{count} PT-BR HTMLs patched (visual refactor)")


if __name__ == "__main__":
    main()
