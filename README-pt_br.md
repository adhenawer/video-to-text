# video-to-text

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/adhenawer/video-to-text)](https://github.com/adhenawer/video-to-text/releases)
[![GitHub Pages](https://img.shields.io/badge/demo-GitHub%20Pages-blue)](https://adhenawer.net/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-MLX-black)](https://github.com/ml-explore/mlx)

> 🇺🇸 **[Read this in English](README.md)** · 🇧🇷 Você está lendo em português brasileiro

Transforma vídeos e podcasts do YouTube e Twitter/X em posts para leitura — organizados por seções e publicados como HTML estático

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
git clone https://github.com/<SEU-USUARIO>/video-to-text
cd video-to-text
python3 -m venv .venv && source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate                              # Windows PowerShell
pip install -r requirements.txt
```

O `requirements.txt` inclui `youtube-transcript-api`, `yt-dlp`, `mlx-whisper`, `mlx-vlm` e outras.

### 3. Instalar dependências do Whisper (hardware)

O Whisper roda **localmente** — sem chamadas de API, sem custo externo. Os requisitos dependem do hardware:

#### Apple Silicon (macOS, recomendado)

Usa [`mlx-whisper`](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — framework MLX otimizado nativamente para chips M1/M2/M3/M4.

```bash
# ffmpeg é necessário pelo yt-dlp para extrair áudio
brew install ffmpeg

# mlx-whisper já foi instalado via requirements.txt
# O modelo (~1.5GB) é baixado automaticamente na primeira execução:
#   mlx-community/whisper-large-v3-turbo
```

Recomendado: M1 Pro 16GB ou superior. Transcrição roda a ~5× a velocidade real.

#### Windows (CPU ou GPU CUDA)

`mlx-whisper` é exclusivo Apple. No Windows, troque por [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) (baseado em CTranslate2):

```powershell
# Instalar ffmpeg (PowerShell como admin)
winget install Gyan.FFmpeg

# No venv
pip uninstall mlx-whisper mlx-vlm mlx-lm -y
pip install faster-whisper

# Com GPU NVIDIA, instale PyTorch CUDA para acelerar:
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Você vai precisar ajustar `src/providers/twitter.py` para chamar `faster_whisper.WhisperModel` em vez de `mlx_whisper.transcribe`. O Claude Code faz esse patch em segundos — peça: *"Troca mlx-whisper por faster-whisper em src/providers/twitter.py mantendo a mesma interface."*

GPU: NVIDIA com 8GB+ VRAM para o modelo `large-v3`, ou use `medium`/`small` em CPU.

#### Linux (CPU ou CUDA)

Igual ao Windows — use `faster-whisper`. Instale `ffmpeg` pelo gerenciador (`apt install ffmpeg` / `dnf install ffmpeg`).

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

### Exemplo Windows

Abra o PowerShell, ative o venv, inicie o Claude Code:

```powershell
cd C:\code\video-to-text
.venv\Scripts\activate
claude
```

Mesma conversa. Para vídeos do Twitter/X, garanta que fez o swap para `faster-whisper` conforme o setup — o Claude Code consegue detectar o ambiente Windows e fazer isso automaticamente.

### Fluxo Twitter/X

```
> transcreve https://x.com/user/status/1234567890
```

Por baixo:

- `yt-dlp` baixa o áudio para `/tmp/`
- `mlx-whisper` (macOS) ou `faster-whisper` (Windows/Linux) transcreve localmente
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

### Deploy

```bash
cd workers/markdown-agent
npm install
npx wrangler login          # primeira vez
npx wrangler deploy
```

---

## Features de leitura

- **3 temas**: ☀️ Sépia (padrão, estilo Kindle) · 🌤️ Claro · 🌙 Escuro
- **Progresso por dispositivo** — cada dispositivo salva a posição independentemente
- **Retomada automática** — banner "continuar de onde parou" ao reabrir
- **Barra de progresso** e % lido fixos durante a rolagem
- **Índice clicável** com todas as seções
- Responsivo para mobile
