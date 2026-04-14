#!/usr/bin/env python3
"""
Fix language switcher links in PT-BR HTMLs that don't have an EN counterpart.
- Duplicates: redirect to canonical EN version
- No EN (Chinese, failed): remove the EN button
"""
import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTBR_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")

# Map: slug without EN -> canonical EN slug (or None to remove button)
CANONICAL = {
    "amit-insights-tecnicos": "obsidian-claude-code-pensamento",
    "ronycoder-arte-comunicar": "entendendo-rony-coder",
    "ronycoder-video": "entendendo-rony-coder",
    "teste-gemma4-pipeline": "de-ides-para-agentes-de-ia-steve-yegge",
    "teste-pipeline-local": "de-ides-para-agentes-de-ia-steve-yegge",
    "dario-amodei-scaling-rl-agi-futuro-anthropic": None,  # no video
    "trading-com-order-flow-mercado-global-ao-chines": None,  # chinese
}


def fix_html(path, slug):
    with open(path) as f:
        html = f.read()

    canonical = CANONICAL.get(slug, "MISSING")
    if canonical == "MISSING":
        return False

    if canonical:
        # Update href to canonical EN
        new_href = f"../original/{canonical}.html"
        html = re.sub(
            r'<a class="lang-btn" href="[^"]*" aria-label="English">🇺🇸 English</a>',
            f'<a class="lang-btn" href="{new_href}" aria-label="English">🇺🇸 English</a>',
            html,
            count=1,
        )
    else:
        # Remove the EN button entirely (keep only PT-BR button)
        html = re.sub(
            r'\s*<a class="lang-btn" href="[^"]*" aria-label="English">🇺🇸 English</a>',
            '',
            html,
            count=1,
        )

    with open(path, "w") as f:
        f.write(html)
    return True


def main():
    count = 0
    for slug in CANONICAL:
        path = os.path.join(PTBR_DIR, f"{slug}.html")
        if not os.path.exists(path):
            print(f"  MISS {slug} — file not found")
            continue
        if fix_html(path, slug):
            target = CANONICAL[slug] or "REMOVED"
            print(f"  OK   {slug} -> {target}")
            count += 1
    print(f"\n{count} arquivos ajustados")


if __name__ == "__main__":
    main()
