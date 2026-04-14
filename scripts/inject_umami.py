#!/usr/bin/env python3
"""Inject Umami analytics snippet into all HTMLs under docs/."""
import os

SNIPPET = '<script defer src="https://cloud.umami.is/script.js" data-website-id="40c8ae3d-2e6b-4af4-a89b-f578dd3b2315"></script>'

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")


def inject(path):
    with open(path) as f:
        html = f.read()
    if "cloud.umami.is" in html:
        return False
    if "</head>" not in html:
        return False
    html = html.replace("</head>", SNIPPET + "\n</head>", 1)
    with open(path, "w") as f:
        f.write(html)
    return True


def main():
    count = 0
    skipped = 0
    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith(".html"):
                if inject(os.path.join(root, f)):
                    count += 1
                else:
                    skipped += 1
    print(f"{count} injected, {skipped} skipped (already had it or no </head>)")


if __name__ == "__main__":
    main()
