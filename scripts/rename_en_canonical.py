#!/usr/bin/env python3
"""
Generate canonical English slugs from EN titles and rename HTML files.
Also updates:
- transcripts/index.json with slug_en field
- PT-BR HTMLs: updates the 🇺🇸 English link href
"""
import json
import os
import re
import sys
import unicodedata

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "original")
PTBR_DIR = os.path.join(PROJECT_DIR, "docs", "posts", "pt_br")
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")

STOPWORDS = {
    "a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to",
    "with", "is", "it", "that", "this", "what", "you", "your", "are", "be",
    "as", "from", "if"
}


def slugify(text):
    """Convert title to URL slug — lowercase, ASCII, hyphens, drop stopwords."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    words = [w for w in re.split(r"[\s_-]+", text) if w and w not in STOPWORDS]
    return "-".join(words)[:80]


def extract_title(html_path):
    with open(html_path) as f:
        html = f.read()
    m = re.search(r"<h1>([^<]+)</h1>", html)
    return m.group(1).strip() if m else None


def main():
    with open(INDEX_PATH) as f:
        index = json.load(f)

    # Build mapping: pt_slug -> en_slug
    mapping = {}  # pt_slug -> en_slug
    for entry in index:
        pt_slug = entry["slug"]
        en_html = os.path.join(ORIGINAL_DIR, f"{pt_slug}.html")
        if not os.path.exists(en_html):
            print(f"  SKIP {pt_slug} — no EN HTML")
            continue
        en_title = extract_title(en_html)
        if not en_title:
            print(f"  SKIP {pt_slug} — no title found")
            continue
        en_slug = slugify(en_title)
        if not en_slug:
            print(f"  SKIP {pt_slug} — slug empty from title '{en_title}'")
            continue
        if en_slug in mapping.values():
            # Deduplicate
            en_slug = f"{en_slug}-{entry['video_id'][:6]}"
        mapping[pt_slug] = en_slug
        entry["slug_en"] = en_slug
        print(f"  {pt_slug}\n  →  {en_slug}\n")

    # Rename HTML files and update internal PT-BR link inside each EN HTML
    for pt_slug, en_slug in mapping.items():
        old_path = os.path.join(ORIGINAL_DIR, f"{pt_slug}.html")
        new_path = os.path.join(ORIGINAL_DIR, f"{en_slug}.html")

        with open(old_path) as f:
            html = f.read()

        # The PT-BR button in EN HTML points to ../pt_br/{pt_slug}.html which stays correct
        # But other internal references may need updating — for now just rename

        with open(new_path, "w") as f:
            f.write(html)
        os.remove(old_path)

    # Update PT-BR HTMLs: change 🇺🇸 English href to new en_slug
    for pt_slug, en_slug in mapping.items():
        pt_path = os.path.join(PTBR_DIR, f"{pt_slug}.html")
        if not os.path.exists(pt_path):
            continue
        with open(pt_path) as f:
            html = f.read()
        old_ref = f'../original/{pt_slug}.html'
        new_ref = f'../original/{en_slug}.html'
        html = html.replace(old_ref, new_ref)
        with open(pt_path, "w") as f:
            f.write(html)

    # Fix duplicates (ronycoder, amit, teste) that point to canonicals already
    # Their EN link points to e.g. ../original/obsidian-claude-code-pensamento.html
    # but that file was renamed to ../original/obsidian-claude-code-second-brain-amplified.html
    # So re-run the replace across all PT-BR HTMLs
    for fname in os.listdir(PTBR_DIR):
        if not fname.endswith(".html"):
            continue
        pt_path = os.path.join(PTBR_DIR, fname)
        with open(pt_path) as f:
            html = f.read()
        original_html = html
        for pt_slug, en_slug in mapping.items():
            html = html.replace(f'../original/{pt_slug}.html', f'../original/{en_slug}.html')
        if html != original_html:
            with open(pt_path, "w") as f:
                f.write(html)

    # Save updated index
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n{len(mapping)} arquivos renomeados + links atualizados")
    return mapping


if __name__ == "__main__":
    main()
