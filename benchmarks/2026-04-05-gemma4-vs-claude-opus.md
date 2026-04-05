# Benchmark: Gemma 4 E4B 8bit vs Claude Opus 4.6

**Data:** 2026-04-05
**Vídeo fonte:** [De IDEs para Agentes de IA — Steve Yegge (Sourcegraph Podcast)](https://youtu.be/aFsAOu2bgFk)
**Transcrição:** 20.562 palavras (inglês)

## Setup

| | Claude Opus 4.6 | Gemma 4 E4B 8bit |
|---|---|---|
| **Execução** | API Anthropic (cloud) | Local, Mac M1 Pro 16GB |
| **Modelo** | claude-opus-4-6 | mlx-community/gemma-4-e4b-it-8bit |
| **Tamanho** | N/A (cloud) | ~8GB |
| **Framework** | Anthropic API | mlx-vlm 0.4.4 |
| **Tempo total** | ~2min | ~5min |
| **Chunking** | Não (contexto 200K) | 4 chunks de ~5-8K palavras |

## Output

| | Claude Opus 4.6 | Gemma 4 E4B 8bit |
|---|---|---|
| **Seções (h2)** | 7 | 9 |
| **Parágrafos** | 34 | 106 |
| **Palavras geradas** | ~3.200 | ~3.300 |
| **Seções fantasma** | 0 | ~20 (sub-seções em MAIÚSCULO renderizadas como `<p>`) |
| **HTML gerado** | artigo limpo | artefatos de markdown (listas `* **Nível:**`) |

## Critérios de avaliação (0-10)

| Critério | Descrição |
|----------|-----------|
| **Fidelidade** | Conteúdo fiel ao original, sem inventar informação |
| **Fluência PT-BR** | Naturalidade do português brasileiro |
| **Organização** | Qualidade das seções temáticas (agrupamento lógico, não cronológico) |
| **Concisão** | Elimina redundâncias, vai direto ao ponto |
| **Formato** | Conformidade com o template (separadores, headings, sem artefatos) |
| **Legibilidade** | Parágrafos bem dimensionados, fáceis de consumir no celular |
| **Cobertura** | Quanto do conteúdo relevante do vídeo foi capturado |

## Pontuação

| Critério | Claude Opus 4.6 | Gemma 4 E4B | Notas |
|----------|:---:|:---:|---|
| Fidelidade | 9 | 7 | Gemma erra o nome: "Steve Yagi" em vez de "Steve Yegge" |
| Fluência PT-BR | 10 | 7 | Gemma repete estruturas ("Ele observou...", "Ele argumentou...", "Ele concluiu...") |
| Organização | 9 | 6 | Claude: 7 seções claras. Gemma: 9 no TOC + ~20 sub-seções soltas no corpo |
| Concisão | 9 | 5 | Gemma repete "efeito vampiro" em 3 locais diferentes do artigo |
| Formato | 10 | 6 | Gemma gera listas markdown que renderizam como texto plano no HTML |
| Legibilidade | 9 | 6 | Claude: parágrafos 3-5 linhas. Gemma: alterna entre 1 linha e blocos densos |
| Cobertura | 8 | 8 | Empate — ambos cobrem os temas principais |
| **Total** | **64/70** | **45/70** | |

## Problemas específicos do Gemma 4 E4B

1. **Nome errado** — "Steve Yagi" consistente no artigo inteiro (nome correto: Steve Yegge)
2. **Sub-seções fantasma** — O modelo gera separadores `====` para sub-seções que o `build_html.py` não reconhece como headings (ficam como parágrafos em MAIÚSCULO)
3. **Markdown no output** — Listas `* **Nível 1:**` que deveriam ser texto corrido aparecem como markdown cru no HTML
4. **Repetição entre chunks** — Mesmo tema abordado em chunks diferentes resulta em conteúdo duplicado (efeito vampiro, captura de valor, inovação em grandes empresas)
5. **Construções robotizadas** — Parágrafos consecutivos começando com "Ele observou que...", "Ele argumentou que...", "Ele concluiu que..."

## Conclusão

O Claude Opus 4.6 produz artigos de qualidade editorial — texto natural, zero erros factuais em nomes, organização limpa, sem repetição. Lê como um artigo escrito por jornalista.

O Gemma 4 E4B 8bit produz conteúdo utilizável mas com problemas claros que exigiriam revisão humana ou pós-processamento para atingir o padrão dos artigos existentes. Para uso pessoal com revisão rápida é aceitável; para publicação direta, o Claude é significativamente superior.

## Arquivos de referência

- Claude Opus 4.6: `leituras/de-ides-para-agentes-de-ia-steve-yegge.html`
- Gemma 4 E4B: `leituras/teste-gemma4-pipeline.html`
