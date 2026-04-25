#!/usr/bin/env python3
"""Backfill title_en in transcripts/index.json from each EN HTML's <h1>.

Run once after introducing the title_en field. Subsequent posts should add
title_en directly to index.json at insertion time.
"""
import json
import os
import re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")
EN_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "original")


def extract_title(html_path):
    if not os.path.exists(html_path):
        return None
    with open(html_path) as f:
        html = f.read()
    # Prefer the og:title (cleaner, no site suffix), fallback to <h1>, then <title>
    m = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    if m:
        return m.group(1).strip()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if m:
        t = m.group(1).strip()
        # strip site suffix like " — Site"
        t = re.sub(r"\s+[—-]\s+.+$", "", t)
        return t
    return None


def main():
    with open(INDEX_PATH) as f:
        index = json.load(f)

    misses = []
    for entry in index:
        slug_en = entry.get("slug_en")
        if not slug_en:
            misses.append(entry["slug"])
            continue
        path = os.path.join(EN_DIR, f"{slug_en}.html")
        title = extract_title(path)
        if title:
            entry["title_en"] = title
        else:
            misses.append(entry["slug"])

    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"backfilled title_en on {len(index) - len(misses)} entries")
    if misses:
        print(f"missed: {misses}")


if __name__ == "__main__":
    main()
