#!/usr/bin/env python3
"""
Translate YouTube transcripts to organized PT-BR articles using a local LLM via mlx-lm.
Default model: Gemma 4 26B-A4B Q4_K_M (mlx-community/gemma-3-27b-it-qat-4bit).

Usage:
    python3 scripts/translate_local.py /tmp/transcript.txt /tmp/output_pt.txt
    python3 scripts/translate_local.py input.txt output.txt --model mlx-community/gemma-3-12b-it-4bit
"""

import argparse
import gc
import re
import sys
import time

DEFAULT_MODEL = "mlx-community/gemma-3-27b-it-qat-4bit"
FALLBACK_MODEL = "mlx-community/gemma-3-12b-it-4bit"
SEPARATOR = "=" * 80

SYSTEM_PROMPT = """\
Você é um tradutor e editor profissional. Transforme a transcrição de vídeo do YouTube abaixo em um artigo organizado em português brasileiro (PT-BR).

REGRAS:
- Escreva em português brasileiro natural e fluente
- Organize em seções temáticas (não cronológicas)
- Remova todos os timestamps, [music], [applause], propagandas, menções a patrocinadores e vícios de linguagem oral
- Cada seção deve ter um título descritivo em MAIÚSCULO
- Use aspas tipográficas (\u201c \u201d) para citações
- Não adicione informações que não estejam na transcrição
- Não crie seções genéricas de "Introdução" ou "Conclusão" a menos que o vídeo tenha

FORMATO DE SAÍDA (siga exatamente):
================================================================================
TÍTULO DA SEÇÃO EM MAIÚSCULO

Conteúdo do parágrafo aqui. Múltiplos parágrafos separados por linhas em branco.

Outro parágrafo nesta seção.

================================================================================
PRÓXIMA SEÇÃO

Conteúdo da próxima seção..."""

STRICT_SUFFIX = """

ATENÇÃO: Sua resposta DEVE começar com uma linha de 80 caracteres '=' seguida do título da primeira seção em MAIÚSCULO. NÃO escreva nada antes do primeiro separador."""


def preprocess(text):
    """Remove timestamps, tags and noise from raw transcript."""
    text = re.sub(r'^\d+:\d+:?\d*\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[(?:music|applause|laughter|Music|Applause)\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_chunks(text, max_words=8000, overlap=500):
    """Split text into chunks at sentence boundaries with overlap."""
    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)

        # Find last sentence boundary (. ! ?) to avoid cutting mid-sentence
        if end < len(words):
            last_period = max(chunk_text.rfind('. '), chunk_text.rfind('? '), chunk_text.rfind('! '))
            if last_period > len(chunk_text) * 0.5:
                chunk_text = chunk_text[:last_period + 1]
                end = start + len(chunk_text.split())

        chunks.append(chunk_text)
        start = max(start + 1, end - overlap)

    return chunks


def validate_output(text):
    """Check that output has the expected section format."""
    return text.count(SEPARATOR) >= 2


def merge_chunks(outputs):
    """Merge translated chunks, removing duplicate separators."""
    merged = outputs[0]
    for chunk_output in outputs[1:]:
        # Remove leading separator from subsequent chunks to avoid duplication
        cleaned = chunk_output.strip()
        if cleaned.startswith(SEPARATOR):
            cleaned = cleaned[len(SEPARATOR):].strip()
        merged = merged.rstrip() + '\n\n' + SEPARATOR + '\n' + cleaned
    return merged


def load_model(model_id):
    """Load model with memory management for 16GB machines."""
    gc.collect()

    try:
        import mlx.core as mx
        mx.metal.set_cache_limit(0)
    except Exception:
        pass

    try:
        from mlx_lm import load
        print(f"Carregando modelo: {model_id}", file=sys.stderr)
        t0 = time.time()
        model, tokenizer = load(model_id)
        print(f"Modelo carregado em {time.time() - t0:.1f}s", file=sys.stderr)
        return model, tokenizer
    except Exception as e:
        if 'memory' in str(e).lower() or 'oom' in str(e).lower() or 'alloc' in str(e).lower():
            print(f"\nERRO: Memória insuficiente para {model_id}.", file=sys.stderr)
            print(f"Tente com modelo menor: --model {FALLBACK_MODEL}", file=sys.stderr)
            sys.exit(1)
        raise


def generate_translation(model, tokenizer, transcript, strict=False):
    """Generate translation using the local model."""
    from mlx_lm import generate

    prompt = SYSTEM_PROMPT
    if strict:
        prompt += STRICT_SUFFIX

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"TRANSCRIÇÃO:\n{transcript}"}
    ]

    # Apply chat template
    if hasattr(tokenizer, 'apply_chat_template'):
        formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        formatted = f"{prompt}\n\nTRANSCRIÇÃO:\n{transcript}"

    print("Gerando tradução...", file=sys.stderr)
    t0 = time.time()

    result = generate(
        model,
        tokenizer,
        prompt=formatted,
        max_tokens=8192,
        temp=0.3,
        repetition_penalty=1.1,
        verbose=False,
    )

    elapsed = time.time() - t0
    print(f"Geração concluída em {elapsed:.1f}s ({len(result.split())} palavras)", file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description="Translate transcript to PT-BR article via local LLM")
    parser.add_argument("input", help="Path to raw transcript .txt")
    parser.add_argument("output", help="Path to save organized PT-BR .txt")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help=f"MLX model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-words-per-chunk", type=int, default=8000, help="Max words per chunk (default: 8000)")
    args = parser.parse_args()

    # Read and preprocess
    with open(args.input, 'r') as f:
        raw = f.read()

    transcript = preprocess(raw)
    word_count = len(transcript.split())
    print(f"Transcrição: {word_count} palavras", file=sys.stderr)

    # Load model
    model, tokenizer = load_model(args.model)

    # Split into chunks if needed
    chunks = split_chunks(transcript, max_words=args.max_words_per_chunk)
    if len(chunks) > 1:
        print(f"Dividido em {len(chunks)} chunks", file=sys.stderr)

    # Translate each chunk
    outputs = []
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"\n--- Chunk {i + 1}/{len(chunks)} ---", file=sys.stderr)

        result = generate_translation(model, tokenizer, chunk)

        # Validate and retry once with stricter prompt if needed
        if not validate_output(result):
            print("Output sem formato correto, retentando com prompt mais restritivo...", file=sys.stderr)
            result = generate_translation(model, tokenizer, chunk, strict=True)
            if not validate_output(result):
                print("AVISO: output pode não estar no formato esperado pelo build_html.py", file=sys.stderr)

        outputs.append(result)

    # Merge and save
    final = merge_chunks(outputs) if len(outputs) > 1 else outputs[0]

    with open(args.output, 'w') as f:
        f.write(final)

    section_count = final.count(SEPARATOR)
    print(f"\nSalvo em {args.output} ({section_count} seções)", file=sys.stderr)


if __name__ == '__main__':
    main()
