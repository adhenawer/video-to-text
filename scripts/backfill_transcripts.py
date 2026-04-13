#!/usr/bin/env python3
"""
Backfill transcripts for all existing articles.
Extracts video URLs from HTML files, fetches transcripts, and updates index.json.
"""
import json
import os
import re
import sys
from datetime import date

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))
from providers import detect_provider


def extract_articles():
    """Extract metadata from all HTML files."""
    leituras = os.path.join(PROJECT_DIR, "docs", "leituras")
    articles = []
    seen_ids = set()

    for fname in sorted(os.listdir(leituras)):
        if not fname.endswith(".html"):
            continue
        path = os.path.join(leituras, fname)
        with open(path) as f:
            html = f.read()

        slug = fname.replace(".html", "")
        title = re.search(r'<h1>([^<]+)</h1>', html)
        title = title.group(1) if title else ""
        cite = re.search(r'<cite>([^<]+)</cite>', html)
        subtitle = cite.group(1) if cite else ""
        url_match = re.search(r'<a href="(https?://[^"]+)"[^>]*target="_blank"', html)
        url = url_match.group(1) if url_match else ""

        if not url:
            print(f"  SKIP {slug} — sem URL")
            continue

        provider = detect_provider(url)
        if provider is None:
            print(f"  SKIP {slug} — provider desconhecido: {url}")
            continue

        video_id = provider.extract_id(url)

        # Skip duplicates (same video_id)
        if video_id in seen_ids:
            print(f"  SKIP {slug} — duplicado de {video_id}")
            continue
        seen_ids.add(video_id)

        articles.append({
            "slug": slug,
            "title": title,
            "subtitle": subtitle,
            "url": url,
            "provider": provider,
            "video_id": video_id,
        })

    return articles


def main():
    articles = extract_articles()
    print(f"\n{len(articles)} vídeos únicos para processar\n")

    index_path = os.path.join(PROJECT_DIR, "transcripts", "index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = []
    existing_ids = {e["video_id"] for e in index}

    youtube_articles = [a for a in articles if a["provider"].name == "youtube"]
    twitter_articles = [a for a in articles if a["provider"].name == "twitter"]

    print(f"YouTube: {len(youtube_articles)} vídeos")
    print(f"Twitter: {len(twitter_articles)} vídeos\n")

    # Process YouTube (fast — API calls)
    for i, art in enumerate(youtube_articles, 1):
        vid = art["video_id"]
        dest = os.path.join(PROJECT_DIR, "transcripts", "youtube", f"{vid}.txt")

        if os.path.exists(dest):
            print(f"  [{i}/{len(youtube_articles)}] EXISTE youtube/{vid}.txt — {art['slug']}")
        else:
            print(f"  [{i}/{len(youtube_articles)}] YouTube {vid} — {art['slug']}...", end=" ", flush=True)
            try:
                text = art["provider"].fetch_transcript(art["url"], timestamps=True)
                with open(dest, "w") as f:
                    f.write(text)
                print(f"OK ({len(text.split())} palavras)")
            except Exception as e:
                print(f"ERRO: {e}")
                continue

        # Update index
        if vid not in existing_ids:
            index.append({
                "video_id": vid,
                "provider": "youtube",
                "title": art["title"],
                "subtitle": art["subtitle"],
                "url": art["url"],
                "slug": art["slug"],
                "date": str(date.today()),
            })
            existing_ids.add(vid)

    # Process Twitter/X (slow — download + Whisper)
    for i, art in enumerate(twitter_articles, 1):
        vid = art["video_id"]
        dest = os.path.join(PROJECT_DIR, "transcripts", "twitter", f"{vid}.txt")

        if os.path.exists(dest):
            print(f"  [{i}/{len(twitter_articles)}] EXISTE twitter/{vid}.txt — {art['slug']}")
        else:
            print(f"  [{i}/{len(twitter_articles)}] Twitter {vid} — {art['slug']}...", end=" ", flush=True)
            try:
                text = art["provider"].fetch_transcript(art["url"], timestamps=True)
                with open(dest, "w") as f:
                    f.write(text)
                print(f"OK ({len(text.split())} palavras)")
            except Exception as e:
                print(f"ERRO: {e}")
                continue

        # Update index
        if vid not in existing_ids:
            index.append({
                "video_id": vid,
                "provider": "twitter",
                "title": art["title"],
                "subtitle": art["subtitle"],
                "url": art["url"],
                "slug": art["slug"],
                "date": str(date.today()),
            })
            existing_ids.add(vid)

    # Save index
    with open(index_path, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\nindex.json atualizado: {len(index)} entradas")
    print("Concluído!")


if __name__ == "__main__":
    main()
