#!/usr/bin/env python3
"""
Full pipeline: YouTube URL → translated PT-BR HTML article.

Default: Claude (via Hermes) handles translation.
With --local: uses local LLM (Gemma 4) for translation.

Usage:
    # Default (Claude traduz)
    python3 scripts/pipeline.py 'https://youtu.be/VIDEO_ID' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo'

    # Local (Gemma 4 traduz)
    python3 scripts/pipeline.py 'https://youtu.be/VIDEO_ID' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo' --local

    # Local com modelo específico
    python3 scripts/pipeline.py 'https://youtu.be/VIDEO_ID' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo' \
      --local --model mlx-community/gemma-4-e4b-it-4bit
"""

import argparse
import os
import re
import subprocess
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)


def extract_video_id(url_or_id):
    """Extract 11-char video ID from YouTube URL."""
    url_or_id = url_or_id.strip()
    for pattern in [
        r'(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def run_step(label, cmd, timeout=600):
    """Run a subprocess step, printing status and timing."""
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
    parser = argparse.ArgumentParser(description="Pipeline: YouTube URL → HTML article")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--title", "-t", required=True, help="Article title")
    parser.add_argument("--subtitle", "-s", required=True, help="Subtitle (source/author)")
    parser.add_argument("--slug", required=True, help="URL slug for the HTML file (e.g. 'meu-artigo')")
    parser.add_argument("--local", action="store_true",
                        help="Use local LLM (Gemma 4) instead of Claude for translation")
    parser.add_argument("--model", "-m", default=None,
                        help="MLX model ID for --local mode (overrides translate_local.py default)")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    transcript_path = f"/tmp/transcript_{video_id}.txt"
    translated_path = f"/tmp/{video_id}_pt.txt"
    html_path = os.path.join(PROJECT_DIR, "leituras", f"{args.slug}.html")

    engine = "local (LLM)" if args.local else "Claude (default)"
    total_t0 = time.time()
    print(f"Pipeline: {args.url}")
    print(f"  Video ID:  {video_id}")
    print(f"  Título:    {args.title}")
    print(f"  Slug:      {args.slug}")
    print(f"  Engine:    {engine}")
    print(f"  Output:    {html_path}")

    # Step 1: Fetch transcript
    print(f"\n{'=' * 60}")
    print(f"  1/3  Capturando transcrição")
    print(f"{'=' * 60}")
    t0 = time.time()
    fetch_result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "fetch_transcript.py"),
         args.url, "--text-only", "--timestamps"],
        capture_output=True, text=True, timeout=60,
    )
    if fetch_result.returncode != 0:
        print(f"ERRO ao capturar transcrição: {fetch_result.stderr}", file=sys.stderr)
        sys.exit(1)
    with open(transcript_path, 'w') as f:
        f.write(fetch_result.stdout)
    print(f"  Salvo em {transcript_path} ({len(fetch_result.stdout.split())} palavras)")
    print(f"  Concluído em {time.time() - t0:.1f}s")

    # Step 2: Translate
    if args.local:
        # Local LLM translation
        translate_cmd = [
            sys.executable, os.path.join(SCRIPTS_DIR, "translate_local.py"),
            transcript_path, translated_path,
        ]
        if args.model:
            translate_cmd.extend(["--model", args.model])
        run_step("2/3  Traduzindo via modelo local", translate_cmd, timeout=600)
    else:
        # Claude translation — pause for user/Hermes to translate
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

        # Check if translated file already exists
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
    run_step(
        "3/3  Gerando HTML",
        [sys.executable, os.path.join(SCRIPTS_DIR, "build_html.py"),
         video_id, args.title, args.subtitle, args.url, translated_path, html_path],
    )

    total_elapsed = time.time() - total_t0
    print(f"\n{'=' * 60}")
    print(f"  Pipeline concluído em {total_elapsed:.1f}s")
    print(f"  Engine:  {engine}")
    print(f"  HTML:    {html_path}")
    print(f"{'=' * 60}")
    print(f"\nPróximos passos:")
    print(f"  1. Adicionar card no index.html")
    print(f"  2. git add leituras/{args.slug}.html index.html")
    print(f"  3. git commit -m 'feat: adiciona artigo — {args.title}'")


if __name__ == '__main__':
    main()
