#!/usr/bin/env python3
"""Strip decorative emojis from index and blog pages per the visual refactor."""
import os
import re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    "docs/index.html",
    "docs/en/index.html",
    "docs/blog/index.html",
    "docs/blog/en/index.html",
]

# List of (pattern, replacement) tuples to apply to each file.
REPLACEMENTS = [
    # h1 title emojis
    (r'<h1>📚 Leituras ', '<h1>Leituras '),
    (r'<h1>📚 Readings ', '<h1>Readings '),
    (r'<h1>📝 Blog</h1>', '<h1>Blog</h1>'),
    (r'<h1>📝 Blog<a', '<h1>Blog<a'),
    # brand emoji in header
    (r'>🎙\s*Leituras</a>', '>Leituras</a>'),
    (r'>🎙\s*Readings</a>', '>Readings</a>'),
    # lang buttons
    (r'>🇧🇷\s*PT</button>', '>PT</button>'),
    (r'>🇺🇸\s*EN</button>', '>EN</button>'),
    # blog link with emoji
    (r'<a href="blog/">📝 Blog</a>', '<a href="blog/">Blog</a>'),
    (r'<a href="../blog/">📝 Blog</a>', '<a href="../blog/">Blog</a>'),
    # card meta emojis (leading)
    (r'<span>🎙️ ', '<span>'),
    (r'<span>🎥 ', '<span>'),
    (r'<span>🐦 ', '<span>'),
    (r'<span>👤 ', '<span>'),
    (r'<span>📑 ', '<span>'),
    (r'<span>🛠 ', '<span>'),
    (r'<span>📣 ', '<span>'),
    (r'<span>🤖 ', '<span>'),
    (r'<span>⏱ ', '<span>'),
]


def main():
    changed = 0
    for rel in TARGETS:
        path = os.path.join(PROJECT_DIR, rel)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            html = f.read()
        original = html
        for pat, repl in REPLACEMENTS:
            html = re.sub(pat, repl, html)
        if html != original:
            with open(path, "w") as f:
                f.write(html)
            changed += 1
            print(f"  OK {rel}")
        else:
            print(f"  SKIP {rel} (no changes)")
    print(f"\n{changed} files updated")


if __name__ == "__main__":
    main()
