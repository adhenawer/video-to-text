# video-to-text

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/adhenawer/video-to-text)](https://github.com/adhenawer/video-to-text/releases)
[![Demo](https://img.shields.io/badge/demo-adhenawer.net-C17C3E)](https://adhenawer.net/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-MLX-black)](https://github.com/ml-explore/mlx)
[![Cloudflare Workers](https://img.shields.io/badge/edge-Cloudflare%20Workers-F38020)](https://workers.cloudflare.com/)
[![Idiomas](https://img.shields.io/badge/idiomas-PT--BR%20%7C%20EN-brightgreen)](https://adhenawer.net/en/)
[![Artigos](https://img.shields.io/badge/artigos-20%2B-blueviolet)](https://adhenawer.net/)

> 🇺🇸 **[Read this in English](README.md)** · 🇧🇷 Você está lendo em português brasileiro

Transforma vídeos e podcasts do YouTube e Twitter/X em posts para leitura — organizados por seções e publicados como HTML estático.

<p align="center">
  <img src="docs/img/hero.svg" alt="URL → transcrição → tradução → artigo bilíngue" width="820">
</p>

---

## Por que

Vídeo longo é difícil de escanear, citar, pesquisar ou reler. Este projeto transforma vídeos em artigos estruturados que dá para ler de fato.

- **Transcrição local** via Whisper — sem custo de API pra áudio
- **Organização por LLM** em seções temáticas — não um muro cronológico de texto
- **Bilíngue nativo** — PT-BR e inglês com `hreflang` alternates
- **Compatível com agentes** — Cloudflare Worker no plano gratuito serve Markdown via content negotiation (75% menos tokens que HTML)
- **Zero build de frontend** — HTML estático no GitHub Pages

Ao vivo em [adhenawer.net](https://adhenawer.net/) · [Blog](https://adhenawer.net/blog/)

---

## Como funciona

O pipeline detecta automaticamente o provider pela URL e usa a estratégia correta para obter a transcrição:

```
URL do vídeo (YouTube, Twitter/X)
    ↓
src/providers/               — detecta provider, captura transcrição
  ├── youtube.py                 — legendas via youtube-transcript-api
  └── twitter.py                 — áudio via yt-dlp → transcrição via mlx-whisper
    ↓
Claude (tradução)                — traduz para PT-BR, remove timestamps/ads/ruídos,
                                   organiza em seções temáticas
    ↓
src/build_html.py            — gera o HTML com o design system do projeto
    ↓
index.html                       — card adicionado ao índice com descrição e progresso
    ↓
Artigo publicado                 — acessível localmente ou via GitHub Pages
```

---

## Arquitetura multi-provider

O sistema usa uma abstração de providers em `src/providers/` que permite suportar diferentes fontes de vídeo. Cada provider implementa:

| Método | Descrição |
|--------|-----------|
| `detect(url)` | Retorna `True` se o provider reconhece a URL |
| `extract_id(url)` | Extrai o ID único do vídeo/tweet |
| `fetch_transcript(url)` | Retorna texto com timestamps no formato padrão |

### Providers disponíveis

| Provider | Fonte | Estratégia |
|----------|-------|------------|
| **YouTube** | `youtube.com`, `youtu.be` | Legendas via `youtube-transcript-api` |
| **Twitter/X** | `x.com`, `twitter.com` | Download de áudio via `yt-dlp` + transcrição local via `mlx-whisper` (Apple Silicon) |

Para adicionar um novo provider (ex: Vimeo), basta criar um novo módulo em `src/providers/` e registrá-lo em `__init__.py`.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Interface | [Hermes](https://github.com/NousResearch/hermes-agent) — agente via WhatsApp/CLI |
| Modelo | Claude (Anthropic) via Hermes |
| Transcrição (YouTube) | [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) |
| Transcrição (Twitter/X) | [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [mlx-whisper](https://github.com/ml-explore/mlx-examples) |
| Tradução / organização | Claude (LLM) ou Gemma 4 local (mlx-lm) |
| Build | `src/build_html.py` — Python puro, sem dependências externas |
| Frontend | HTML estático — zero frameworks, zero build steps, agora serve markdown também (via Cloudflare Worker) |
| Hosting | GitHub Pages ou qualquer servidor estático |
| Edge / Agentes | Cloudflare Worker (plano Free) — converte HTML→Markdown em runtime via content negotiation |

---

## Setup completo

> **Nota sobre agentes**: este projeto rodava dentro de agentes externos (OpenCode/Hermes) recebendo URLs pelo WhatsApp. A Anthropic bloqueou o uso do token de assinatura em agentes de terceiros, então o fluxo agora roda **direto dentro do [Claude Code](https://claude.com/claude-code)** — a CLI oficial da Anthropic. Você conduz o pipeline conversando com o Claude Code no terminal; ele edita arquivos, roda comandos e faz push no git por você.

### 1. Instalar o Claude Code

```bash
# macOS / Linux / WSL2
curl -fsSL https://claude.ai/install.sh | bash

# Alternativa via npm (qualquer SO)
npm install -g @anthropic-ai/claude-code
```

Rode `claude` em qualquer diretório para iniciar o agente. Na primeira execução pede para logar com sua conta Anthropic (assinatura ou API key).

### 2. Clonar e instalar deps Python

```bash
git clone https://github.com/adhenawer/video-to-text
cd video-to-text
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

O `requirements.txt` inclui `youtube-transcript-api`, `yt-dlp`, `mlx-whisper`, `mlx-vlm` e outras.

### 3. Instalar o Whisper (Apple Silicon)

O Whisper roda **localmente** — sem chamadas de API, sem custo externo. Este projeto usa [`mlx-whisper`](https://github.com/ml-explore/mlx-examples/tree/main/whisper), o framework MLX otimizado nativamente para Apple Silicon (M1/M2/M3/M4).

```bash
# ffmpeg é necessário pelo yt-dlp para extrair áudio
brew install ffmpeg

# mlx-whisper já foi instalado via requirements.txt
# O modelo (~1.5GB) é baixado automaticamente na primeira execução:
#   mlx-community/whisper-large-v3-turbo
```

Hardware recomendado: M1 Pro 16GB ou superior. Transcrição roda a ~5× a velocidade real.

### 4. Rodar o servidor local

```bash
python3 -m http.server 8080
# http://localhost:8080
# Rede local (celular): http://<SEU-IP-LOCAL>:8080
```

---

## Fluxo agêntico detalhado (dentro do Claude Code)

Este é o fluxo exato que uso no dia a dia. Você abre o projeto no Claude Code (`claude` na raiz do repo) e conduz tudo por chat.

### Exemplo macOS

**1. Iniciar o Claude Code no repo**

```bash
cd ~/code/video-to-text
claude
```

**2. Pedir ao Claude Code para processar um vídeo**

```
> adiciona artigo de https://youtu.be/owmJyKVu5f8
```

O Claude Code então, sozinho:

- Roda `python3 src/fetch_transcript.py 'https://youtu.be/owmJyKVu5f8' --text-only --timestamps > /tmp/transcript_owmJyKVu5f8.txt`
- Lê a transcrição, traduz para PT-BR e organiza em seções temáticas, salvando `/tmp/owmJyKVu5f8_pt.txt`
- Chama `python3 src/build_html.py owmJyKVu5f8 'Título' 'Fonte' 'URL' /tmp/owmJyKVu5f8_pt.txt docs/posts/pt_br/SLUG.html`
- Edita `docs/index.html` para adicionar o card
- Atualiza `docs/sitemap.xml` e `docs/llms.txt`
- `git add`, `git commit`, `git push`

Você revisa o diff dentro do Claude Code. Se algo ficou estranho, pede para ele corrigir.

### Fluxo Twitter/X

```
> transcreve https://x.com/user/status/1234567890
```

Por baixo:

- `yt-dlp` baixa o áudio para `/tmp/`
- `mlx-whisper` transcreve localmente no Apple Silicon
- Mesma tradução + geração de HTML do YouTube

### Documentação completa

> Ver [CLAUDE.md](CLAUDE.md) para a base de conhecimento completa que o Claude Code usa para navegar o código.

---

## Markdown for Agents (Cloudflare Worker)

O site serve HTML normal para humanos e **Markdown automático** para agentes de IA que fazem *content negotiation* via `Accept: text/markdown`. Inspirado na feature [Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/) da Cloudflare — que só existe em plano pago — este projeto implementa a mesma ideia usando **Cloudflare Workers no plano gratuito**.

### Por que isso importa

Um HTML de artigo neste site custa ~53.000 tokens para um agente ler (markup, nav, scripts, CSS). A versão Markdown do mesmo conteúdo consome **~13.000 tokens — 75% menos**. Agentes economizam contexto, custo e latência.

### Como funciona

```
Humano (Accept: text/html)
  → Cloudflare edge → GitHub Pages → HTML completo

Agente (Accept: text/markdown)
  → Cloudflare edge → Worker intercepta → fetch HTML → converte → Markdown
```

O Worker roda na edge do Cloudflare (latência ~10ms), consome o HTML do origin (GitHub Pages) e retorna Markdown limpo com frontmatter YAML contendo metadata.

### Teste rápido

```bash
# HTML normal (humano)
curl -sI https://adhenawer.net/posts/pt_br/chefe-do-claude-code-o-que-acontece-depois-que-a-programacao-for-resolvida.html | grep -i content-type
# content-type: text/html; charset=utf-8

# Markdown (agente)
curl -s https://adhenawer.net/posts/pt_br/chefe-do-claude-code-o-que-acontece-depois-que-a-programacao-for-resolvida.html \
  -H "Accept: text/markdown" | head -15
# ---
# title: "Chefe do Claude Code: ..."
# author: "Lenny's Podcast com Boris Cherny ..."
# description: "..."
# source: "https://adhenawer.net/..."
# lang: pt-BR
# ---
#
# ## INTRODUÇÃO
#
# 100% do meu código é escrito pelo Claude Code...
```

Headers de resposta do Worker:

| Header | Valor |
|---|---|
| `Content-Type` | `text/markdown; charset=utf-8` |
| `x-markdown-tokens` | Estimativa de tokens do Markdown retornado |
| `Vary` | `Accept` (para cache correto) |
| `Cache-Control` | `public, max-age=3600` |

### Implementação técnica

Localização: `workers/markdown-agent/`

```
workers/markdown-agent/
├── wrangler.toml       ← rotas e config do Worker
├── package.json
└── src/
    └── index.js        ← lógica: detecta Accept → fetch HTML → converte → retorna
```

**Rotas registradas** (`wrangler.toml`):

```toml
routes = [
  { pattern = "adhenawer.net/posts/*", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/en/*", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/leituras/*", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/index.html", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/llms.txt", zone_name = "adhenawer.net" }
]
```

**Fluxo do Worker** (`src/index.js`, resumo):

A conversão HTML→Markdown é feita com regex puro (sem dependências externas) porque os HTMLs do projeto têm estrutura previsível (`<article>` envolvendo `<h2>`, `<p>`, `<section>`, `<figure class="slide-figure">`). Evita Turndown/JSDOM que não rodam nativamente em Workers runtime.

### Custo

**Zero.** O plano Free do Cloudflare Workers oferece **100.000 requisições/dia sem custo**. Mais que suficiente para um site estático com tráfego moderado de agentes.

### Deploy

```bash
cd workers/markdown-agent
npm install
npx wrangler login          # primeira vez
npx wrangler deploy
```

### Referências

- Post no blog da Cloudflare: [Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/)
- Documentação da feature (pago): [developers.cloudflare.com/fundamentals/reference/markdown-for-agents](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/)

---

## Sidebar de referências

Cada artigo tem uma sidebar fixa (à direita em telas largas, inline em mobile) com referências extraídas da **transcrição no idioma original** via subagentes LLM. Categorias:

| Categoria | Ícone | Link |
|---|---|---|
| Livros | 📖 | Busca no Amazon (`amazon.com/s?k=...`) |
| Ferramentas | 🛠 | Site oficial do produto |
| Papers | 📄 | arXiv / blog do autor |
| Pessoas | 👥 | **Twitter/X prioritário**, fallback para LinkedIn / site pessoal / Wikipedia |
| Conceitos | 🧠 | Wikipedia / transformer-circuits.pub |
| Empresas | 🏢 | Site oficial |
| Posts relacionados | 🔗 | Cross-link interno (para o slug canônico do outro idioma) |

### Como funciona a extração

1. **Fonte da verdade**: transcrição bruta no idioma original (`transcripts/{provider}/{id}.txt`)
2. **Subagentes** (um por post, em paralelo) recebem a transcrição + o schema + o mapeamento de slugs
3. Cada subagente escreve `transcripts/{provider}/{id}.references.json` — o **subproduto persistido**
4. `transcripts/index.json` ganha um resumo por entrada: `references.counts.*` e `references.total`
5. `build_html.py` carrega o JSON automaticamente quando `provider=...` é passado e renderiza a sidebar

### Schema JSON

```json
{
  "video_id": "We7BZVKbCVw",
  "extracted_at": "2026-04-14",
  "books": [{"title":"...","author":"...","url":"...","context":"..."}],
  "tools": [{"name":"...","url":"...","context":"..."}],
  "papers": [{"title":"...","authors":"...","url":"...","context":"..."}],
  "people": [{"name":"...","role":"...","url":"...","context":"..."}],
  "concepts": [{"name":"...","url":"...","context":"..."}],
  "companies": [{"name":"...","url":"..."}],
  "related_posts": [{"slug_pt":"...","slug_en":"...","reason":"..."}]
}
```

### Prioridade em pessoas: Twitter primeiro

O campo `url` do `people[]` segue uma ordem estrita: **handle do Twitter/X primeiro**, depois LinkedIn, depois site pessoal/blog, e Wikipedia apenas como último recurso. Os subagentes de extração tentam derivar o handle do perfil público da pessoa. Para figuras históricas ou acadêmicos falecidos que nunca tiveram Twitter, o campo fica vazio ou aponta para Wikipedia.

O enriquecimento é idempotente: rodar `scripts/enrich_people_twitter.py` aplica uma tabela curada de handles em todos os JSONs de referências sem sobrescrever URLs do Twitter existentes.

### Estatísticas na v2

- **714 referências** extraídas em 21 posts
- Mais ricos: *Estado da IA 2026* (Simon Willison, 61 refs) · *De IDEs para Agentes* (Steve Yegge, 59) · *Finanças Comportamentais* (Shiller, 55)
- Extraído em paralelo por 20 subagentes em ~2 minutos

### Adicionar referências a um novo artigo

Dentro do Claude Code:

```
> extrai referências de transcripts/youtube/{ID}.txt seguindo o schema em CLAUDE.md
> escreve em transcripts/youtube/{ID}.references.json
```

Depois:

```bash
python3 scripts/regen_en_htmls.py         # regera EN HTMLs com sidebar
python3 scripts/patch_ptbr_references.py  # injeta sidebar nos PT-BR existentes
python3 scripts/update_index_references.py  # atualiza contagens no index.json
```

---

## Artigos

O índice completo de artigos está em [adhenawer.net](https://adhenawer.net/) (PT-BR) e [adhenawer.net/en/](https://adhenawer.net/en/) (inglês).
