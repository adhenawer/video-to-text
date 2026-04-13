#!/usr/bin/env python3
"""
Patch existing PT-BR HTMLs after move from docs/leituras/ to docs/posts/pt_br/:
- Fix relative paths (../ -> ../../)
- Add language switcher (🇧🇷 PT-BR / 🇺🇸 EN)
- Update back-home link
"""
import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTBR_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")


def patch_html(path):
    with open(path) as f:
        html = f.read()

    original = html

    # Fix relative paths: ../ -> ../../
    html = html.replace('href="../css/', 'href="../../css/')
    html = html.replace('src="../js/', 'src="../../js/')
    html = html.replace('src="../img/', 'src="../../img/')
    html = html.replace('href="../index.html"', 'href="../../index.html"')

    # Add language switcher next to theme-bar
    slug = os.path.basename(path).replace(".html", "")
    en_link = f"../original/{slug}.html"

    lang_switcher = (
        '  <div class="lang-bar">\n'
        '    <a class="lang-btn active" href="#" aria-label="Português">🇧🇷 Português</a>\n'
        f'    <a class="lang-btn" href="{en_link}" aria-label="English">🇺🇸 English</a>\n'
        '  </div>\n'
    )

    # Insert lang-bar right before theme-bar
    if '<div class="lang-bar">' not in html:
        html = html.replace(
            '  <div class="theme-bar">',
            lang_switcher + '  <div class="theme-bar">',
            1
        )

    if html != original:
        with open(path, "w") as f:
            f.write(html)
        return True
    return False


def main():
    count = 0
    for fname in sorted(os.listdir(PTBR_DIR)):
        if not fname.endswith(".html"):
            continue
        path = os.path.join(PTBR_DIR, fname)
        if patch_html(path):
            print(f"  Patched {fname}")
            count += 1
    print(f"\n{count} arquivos atualizados")


if __name__ == "__main__":
    main()
