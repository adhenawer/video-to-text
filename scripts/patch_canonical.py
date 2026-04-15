#!/usr/bin/env python3
"""
Injeta <link rel="canonical"> em todos os HTMLs que ainda não o têm.

- docs/posts/pt_br/*.html  → canonical apontando para posts/pt_br/{slug}.html
- docs/posts/original/*.html → canonical apontando para posts/original/{slug}.html
- docs/index.html          → canonical https://adhenawer.net/
- docs/en/index.html       → canonical https://adhenawer.net/en/
"""
import os
import re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://adhenawer.net"


def inject_canonical(html_path, canonical_url):
    with open(html_path) as f:
        html = f.read()
    if 'rel="canonical"' in html:
        return False
    tag = f'<link rel="canonical" href="{canonical_url}">\n'
    # Insert right before the first hreflang or, if none, before </head>
    m = re.search(r'(<link rel="alternate" hreflang=)', html)
    if m:
        html = html[:m.start()] + tag + html[m.start():]
    else:
        html = html.replace("</head>", tag + "</head>", 1)
    with open(html_path, "w") as f:
        f.write(html)
    return True


def main():
    count = 0

    pt_dir = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")
    for fn in sorted(os.listdir(pt_dir)):
        if not fn.endswith(".html"):
            continue
        path = os.path.join(pt_dir, fn)
        url = f"{SITE}/posts/pt_br/{fn}"
        if inject_canonical(path, url):
            print(f"  PT  {fn}")
            count += 1

    en_dir = os.path.join(PROJECT_DIR, "docs", "posts", "original")
    for fn in sorted(os.listdir(en_dir)):
        if not fn.endswith(".html"):
            continue
        path = os.path.join(en_dir, fn)
        url = f"{SITE}/posts/original/{fn}"
        if inject_canonical(path, url):
            print(f"  EN  {fn}")
            count += 1

    # Indexes
    for rel, url in [
        ("docs/index.html", f"{SITE}/"),
        ("docs/en/index.html", f"{SITE}/en/"),
        ("docs/moc.html", f"{SITE}/moc.html"),
    ]:
        path = os.path.join(PROJECT_DIR, rel)
        if os.path.exists(path) and inject_canonical(path, url):
            print(f"  IDX {rel}")
            count += 1

    print(f"\n{count} HTMLs patched with canonical")


if __name__ == "__main__":
    main()
