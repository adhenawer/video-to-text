#!/usr/bin/env python3
"""
Full pipeline: Video URL → translated PT-BR HTML article.

Supports: YouTube, Twitter/X.

Default: Claude (via Hermes) handles translation.
With --local: uses local LLM (Gemma 4) for translation.

Usage:
    # YouTube (Claude traduz)
    python3 src/pipeline.py 'https://youtu.be/VIDEO_ID' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo'

    # Twitter/X (Claude traduz)
    python3 src/pipeline.py 'https://x.com/user/status/12345' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo'

    # Local (Gemma 4 traduz)
    python3 src/pipeline.py 'https://youtu.be/VIDEO_ID' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo' --local
"""

import argparse
import json
import os
import shutil
import sys
import time
from datetime import date

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SRC_DIR)

sys.path.insert(0, SRC_DIR)
from providers import detect_provider


def update_transcript_index(index_path, entry):
    """Add or update an entry in transcripts/index.json."""
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            index = json.load(f)
    else:
        index = []

    # Update existing entry or append new one
    for i, existing in enumerate(index):
        if existing["video_id"] == entry["video_id"]:
            index[i] = entry
            break
    else:
        index.append(entry)

    with open(index_path, 'w') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def run_step(label, cmd, timeout=600):
    """Run a subprocess step, printing status and timing."""
    import subprocess
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    t0 = time.time()

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - t0

    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"\nERRO na etapa: {label}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        sys.exit(1)

    print(f"  Concluído em {elapsed:.1f}s")
    return result


def main():
    parser = argparse.ArgumentParser(description="Pipeline: Video URL → HTML article")
    parser.add_argument("url", help="Video URL (YouTube, Twitter/X)")
    parser.add_argument("--title", "-t", required=True, help="Article title")
    parser.add_argument("--subtitle", "-s", required=True, help="Subtitle (source/author)")
    parser.add_argument("--slug", required=True, help="URL slug for the HTML file (e.g. 'meu-artigo')")
    parser.add_argument("--local", action="store_true",
                        help="Use local LLM (Gemma 4) instead of Claude for translation")
    parser.add_argument("--model", "-m", default=None,
                        help="MLX model ID for --local mode (overrides translate_local.py default)")
    parser.add_argument("--slides", action="store_true",
                        help="Extract presentation slides from video (Twitter/X)")
    parser.add_argument("--scene-threshold", type=float, default=0.985,
                        help="Similarity threshold for slide detection (default: 0.985)")
    args = parser.parse_args()

    # Detect provider from URL
    provider = detect_provider(args.url)
    if provider is None:
        print(f"ERRO: URL não reconhecida: {args.url}", file=sys.stderr)
        print("URLs suportadas: YouTube, Twitter/X", file=sys.stderr)
        sys.exit(1)

    video_id = provider.extract_id(args.url)
    transcript_path = f"/tmp/transcript_{video_id}.txt"
    translated_path = f"/tmp/{video_id}_pt.txt"
    html_path = os.path.join(PROJECT_DIR, "docs", "leituras", f"{args.slug}.html")

    # Slides setup
    slides_dir = None
    slides_json = None
    if args.slides:
        slides_dir = os.path.join(PROJECT_DIR, "docs", "img", args.slug)
        os.makedirs(slides_dir, exist_ok=True)
        slides_json = f"/tmp/{video_id}_slides.json"

    engine = "local (LLM)" if args.local else "Claude (default)"
    total_t0 = time.time()
    print(f"Pipeline: {args.url}")
    print(f"  Provider:  {provider.display_name}")
    print(f"  Video ID:  {video_id}")
    print(f"  Título:    {args.title}")
    print(f"  Slug:      {args.slug}")
    print(f"  Engine:    {engine}")
    if args.slides:
        print(f"  Slides:    {slides_dir}")
    print(f"  Output:    {html_path}")

    # Step 1: Fetch transcript via provider
    print(f"\n{'=' * 60}")
    print(f"  1/3  Capturando transcrição ({provider.display_name})")
    print(f"{'=' * 60}")
    t0 = time.time()
    try:
        fetch_kwargs = {"timestamps": True}
        if args.slides:
            fetch_kwargs.update(slides=True, slides_dir=slides_dir, slug=args.slug)
        transcript_text = provider.fetch_transcript(args.url, **fetch_kwargs)
    except RuntimeError as e:
        print(f"ERRO ao capturar transcrição: {e}", file=sys.stderr)
        sys.exit(1)
    with open(transcript_path, 'w') as f:
        f.write(transcript_text)
    print(f"  Salvo em {transcript_path} ({len(transcript_text.split())} palavras)")
    print(f"  Concluído em {time.time() - t0:.1f}s")

    # Step 2: Translate
    if args.local:
        translate_cmd = [
            sys.executable, os.path.join(SRC_DIR, "translate_local.py"),
            transcript_path, translated_path,
        ]
        if args.model:
            translate_cmd.extend(["--model", args.model])
        run_step("2/3  Traduzindo via modelo local", translate_cmd, timeout=600)
    else:
        print(f"\n{'=' * 60}")
        print(f"  2/3  Tradução via Claude")
        print(f"{'=' * 60}")
        print(f"  Transcrição salva em: {transcript_path}")
        print(f"  Traduza com Claude e salve em: {translated_path}")
        print()
        print(f"  Formato esperado:")
        print(f"  ========================================")
        print(f"  NOME DA SEÇÃO EM MAIÚSCULO")
        print()
        print(f"  Parágrafo do conteúdo...")
        print(f"  ========================================")
        print()

        if os.path.exists(translated_path):
            print(f"  Arquivo {translated_path} já existe, usando existente.")
        else:
            print(f"  Aguardando {translated_path}...")
            print(f"  (Ctrl+C para cancelar)")
            try:
                while not os.path.exists(translated_path):
                    time.sleep(2)
            except KeyboardInterrupt:
                print("\nCancelado.")
                sys.exit(0)
            print(f"  Arquivo detectado!")

    # Step 3: Build HTML
    build_cmd = [
        sys.executable, os.path.join(SRC_DIR, "build_html.py"),
        video_id, args.title, args.subtitle, args.url, translated_path, html_path,
        provider.link_text,
    ]
    if args.slides and slides_json and os.path.exists(slides_json):
        build_cmd.append(slides_json)
    run_step("3/3  Gerando HTML", build_cmd)

    # Save transcripts to repo for future reuse (organized by provider)
    transcripts_dir = os.path.join(PROJECT_DIR, "transcripts", provider.name)
    os.makedirs(transcripts_dir, exist_ok=True)
    repo_transcript = os.path.join(transcripts_dir, f"{video_id}.txt")
    repo_translated = os.path.join(transcripts_dir, f"{video_id}_pt.txt")
    shutil.copy2(transcript_path, repo_transcript)
    shutil.copy2(translated_path, repo_translated)

    # Update transcripts/index.json manifest
    index_path = os.path.join(PROJECT_DIR, "transcripts", "index.json")
    update_transcript_index(index_path, {
        "video_id": video_id,
        "provider": provider.name,
        "title": args.title,
        "subtitle": args.subtitle,
        "url": args.url,
        "slug": args.slug,
        "date": str(date.today()),
    })
    print(f"\n  Transcrições salvas em transcripts/{provider.name}/")

    total_elapsed = time.time() - total_t0
    print(f"\n{'=' * 60}")
    print(f"  Pipeline concluído em {total_elapsed:.1f}s")
    print(f"  Provider: {provider.display_name}")
    print(f"  Engine:   {engine}")
    print(f"  HTML:     {html_path}")
    print(f"{'=' * 60}")
    print(f"\nPróximos passos:")
    print(f"  1. Adicionar card no docs/index.html")
    if args.slides:
        print(f"  2. git add docs/leituras/{args.slug}.html docs/img/{args.slug}/ docs/index.html transcripts/")
    else:
        print(f"  2. git add docs/leituras/{args.slug}.html docs/index.html transcripts/")
    print(f"  3. git commit -m 'feat: adiciona artigo — {args.title}'")


if __name__ == '__main__':
    main()
