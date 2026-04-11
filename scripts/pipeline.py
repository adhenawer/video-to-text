#!/usr/bin/env python3
"""
Full pipeline: Video URL → translated PT-BR HTML article.

Supports: YouTube, Twitter/X.

Default: Claude (via Hermes) handles translation.
With --local: uses local LLM (Gemma 4) for translation.

Usage:
    # YouTube (Claude traduz)
    python3 scripts/pipeline.py 'https://youtu.be/VIDEO_ID' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo'

    # Twitter/X (Claude traduz)
    python3 scripts/pipeline.py 'https://x.com/user/status/12345' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo'

    # Local (Gemma 4 traduz)
    python3 scripts/pipeline.py 'https://youtu.be/VIDEO_ID' \
      --title 'Título' --subtitle 'Fonte' --slug 'slug-do-titulo' --local
"""

import argparse
import os
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)

sys.path.insert(0, SCRIPTS_DIR)
from providers import detect_provider


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
    html_path = os.path.join(PROJECT_DIR, "leituras", f"{args.slug}.html")

    engine = "local (LLM)" if args.local else "Claude (default)"
    total_t0 = time.time()
    print(f"Pipeline: {args.url}")
    print(f"  Provider:  {provider.display_name}")
    print(f"  Video ID:  {video_id}")
    print(f"  Título:    {args.title}")
    print(f"  Slug:      {args.slug}")
    print(f"  Engine:    {engine}")
    print(f"  Output:    {html_path}")

    # Step 1: Fetch transcript via provider
    print(f"\n{'=' * 60}")
    print(f"  1/3  Capturando transcrição ({provider.display_name})")
    print(f"{'=' * 60}")
    t0 = time.time()
    try:
        transcript_text = provider.fetch_transcript(args.url, timestamps=True)
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
            sys.executable, os.path.join(SCRIPTS_DIR, "translate_local.py"),
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
        sys.executable, os.path.join(SCRIPTS_DIR, "build_html.py"),
        video_id, args.title, args.subtitle, args.url, translated_path, html_path,
        provider.link_text,
    ]
    run_step("3/3  Gerando HTML", build_cmd)

    total_elapsed = time.time() - total_t0
    print(f"\n{'=' * 60}")
    print(f"  Pipeline concluído em {total_elapsed:.1f}s")
    print(f"  Provider: {provider.display_name}")
    print(f"  Engine:   {engine}")
    print(f"  HTML:     {html_path}")
    print(f"{'=' * 60}")
    print(f"\nPróximos passos:")
    print(f"  1. Adicionar card no index.html")
    print(f"  2. git add leituras/{args.slug}.html index.html")
    print(f"  3. git commit -m 'feat: adiciona artigo — {args.title}'")


if __name__ == '__main__':
    main()
