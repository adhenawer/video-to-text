#!/usr/bin/env python3
"""Patch blog HTMLs to add hreflang alternates and proper lang switcher."""
import os, re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, *, is_en, counterpart_rel):
    """
    is_en: True if this is the English version (at /blog/en/)
    counterpart_rel: relative URL of the other-language version
    """
    with open(path) as f:
        html = f.read()

    # Build hreflang alternates. PT-BR at /blog/<slug>, EN at /blog/en/<slug>
    filename = os.path.basename(path)
    if is_en:
        pt_href = f"../{filename}"   # ../{file}.html → docs/blog/{file}.html
        en_href = filename           # current
    else:
        pt_href = filename           # current
        en_href = f"en/{filename}"   # en/{file}.html → docs/blog/en/{file}.html

    hreflang = (
        f'<link rel="alternate" hreflang="pt-BR" href="{pt_href}">\n'
        f'<link rel="alternate" hreflang="en" href="{en_href}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{pt_href}">\n'
    )

    if 'hreflang="pt-BR"' not in html:
        html = html.replace(
            '<link rel="stylesheet"',
            hreflang + '<link rel="stylesheet"',
            1
        )

    # Replace site-header with one that uses PT/EN switcher
    brand = "Readings" if is_en else "Leituras"
    home_href = "../../index.html" if is_en else "../index.html"
    pt_class = "" if is_en else "active"
    en_class = "active" if is_en else ""

    new_header = (
        f'<header class="site-header">\n'
        f'  <a class="site-brand" href="{home_href}">🎙 {brand}</a>\n'
        f'  <div class="lang-bar">\n'
        f'    <button class="lang-btn {pt_class}" data-lang="pt-BR" aria-label="Português">🇧🇷 PT</button>\n'
        f'    <button class="lang-btn {en_class}" data-lang="en" aria-label="English">🇺🇸 EN</button>\n'
        f'  </div>\n'
        f'</header>'
    )

    html = re.sub(
        r'<header class="site-header">.*?</header>',
        new_header,
        html,
        count=1,
        flags=re.DOTALL
    )

    # Ensure js/lang.js is included
    js_src = "../../js/lang.js" if is_en else "../js/lang.js"
    if 'lang.js' not in html:
        html = html.replace(
            '</body>',
            f'<script src="{js_src}"></script>\n</body>',
            1
        )

    with open(path, 'w') as f:
        f.write(html)


def main():
    en_dir = os.path.join(PROJECT_DIR, "docs", "blog", "en")
    for fname in os.listdir(en_dir):
        if fname.endswith(".html"):
            patch(os.path.join(en_dir, fname), is_en=True, counterpart_rel="")
            print(f"  Patched EN {fname}")


if __name__ == "__main__":
    main()
