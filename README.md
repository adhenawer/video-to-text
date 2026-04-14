# video-to-text

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/adhenawer/video-to-text)](https://github.com/adhenawer/video-to-text/releases)
[![GitHub Pages](https://img.shields.io/badge/demo-GitHub%20Pages-blue)](https://adhenawer.net/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-MLX-black)](https://github.com/ml-explore/mlx)

> 🇧🇷 **[Leia em português brasileiro](README-pt_br.md)** · 🇺🇸 You are reading in English

Turns YouTube and Twitter/X videos and podcasts into readable posts — organized by sections and published as static HTML.

---

## How it works

The pipeline auto-detects the provider from the URL and uses the right strategy to fetch the transcript:

```
Video URL (YouTube, Twitter/X)
    ↓
src/providers/               — detect provider, capture transcript
  ├── youtube.py                 — captions via youtube-transcript-api
  └── twitter.py                 — audio via yt-dlp → transcription via mlx-whisper
    ↓
Claude (translation)             — translates to PT-BR, strips timestamps/ads/noise,
                                   organizes into thematic sections
    ↓
src/build_html.py            — generates HTML with the project's design system
    ↓
index.html                       — card added to the index with description + progress
    ↓
Published article                — accessible locally or via GitHub Pages
```

The site publishes both languages: original (English for most videos) and Brazilian Portuguese. A Cloudflare Worker serves Markdown on demand for AI agents via content negotiation — see the [Markdown for Agents](#markdown-for-agents-cloudflare-worker) section below.

---

## Multi-provider architecture

The system uses a provider abstraction in `src/providers/` that supports different video sources. Each provider implements:

| Method | Description |
|--------|-------------|
| `detect(url)` | Returns `True` if the provider recognizes the URL |
| `extract_id(url)` | Extracts the unique video/tweet ID |
| `fetch_transcript(url)` | Returns text with timestamps in the standard format |

### Available providers

| Provider | Source | Strategy |
|----------|--------|----------|
| **YouTube** | `youtube.com`, `youtu.be` | Captions via `youtube-transcript-api` |
| **Twitter/X** | `x.com`, `twitter.com` | Audio download via `yt-dlp` + local transcription via `mlx-whisper` (Apple Silicon) |

To add a new provider (e.g. Vimeo), create a new module in `src/providers/` and register it in `__init__.py`.

---

## Stack

| Layer | Technology |
|-------|------------|
| Interface | [Hermes](https://github.com/NousResearch/hermes-agent) — agent via WhatsApp/CLI |
| Model | Claude (Anthropic) via Hermes |
| Transcription (YouTube) | [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) |
| Transcription (Twitter/X) | [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [mlx-whisper](https://github.com/ml-explore/mlx-examples) |
| Translation / organization | Claude (LLM) or Gemma 4 local (mlx-lm) |
| Build | `src/build_html.py` — pure Python, no external dependencies |
| Frontend | Static HTML — zero frameworks, zero build steps, now also serves markdown (via Cloudflare Worker) |
| Hosting | GitHub Pages or any static server |
| Edge / Agents | Cloudflare Worker (Free plan) — converts HTML→Markdown at runtime via content negotiation |

---

## Full setup

### 1. Install Hermes

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/src/install.sh | bash
source ~/.bashrc   # or: source ~/.zshrc
hermes             # starts the agent in the terminal
```

Works on Linux, macOS and WSL2. The installer handles Python, Node.js and dependencies.

### 2. Configure model and tools

```bash
hermes model    # choose provider and model (e.g. anthropic:claude-sonnet-4-6)
hermes tools    # enable required tools
```

To use Claude, you need an Anthropic API key in `ANTHROPIC_API_KEY`.

### 3. Connect to WhatsApp (optional, but recommended)

Hermes can receive messages straight from WhatsApp. To set it up:

```bash
hermes gateway setup    # configure messaging platforms
hermes gateway start    # start the gateway
```

Scan the QR code with WhatsApp. Once connected, you send URLs right from the app and receive the generated article.

> Also works via Telegram, Discord, Slack or directly in the terminal with `hermes`.

### 4. Clone this repo

```bash
git clone https://github.com/<YOUR-USERNAME>/video-to-text
cd video-to-text
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the local server

```bash
python3 -m http.server 8080
# http://localhost:8080
# Local network (phone): http://<YOUR-LOCAL-IP>:8080
```

---

## Usage via pipeline

### YouTube (Claude translates)

```bash
python3 src/pipeline.py \
  'https://youtu.be/VIDEO_ID' \
  --title 'Article title' \
  --subtitle 'Source / Channel' \
  --slug 'article-slug'
```

### Twitter/X (Claude translates)

```bash
python3 src/pipeline.py \
  'https://x.com/user/status/TWEET_ID' \
  --title 'Article title' \
  --subtitle 'Source / Channel' \
  --slug 'article-slug'
```

### Local translation (Gemma 4)

```bash
python3 src/pipeline.py \
  'VIDEO_URL' \
  --title 'Title' --subtitle 'Source' --slug 'slug' \
  --local
```

The pipeline auto-detects the provider from the URL.

---

## Detailed agentic flow

This is the exact flow I use daily via WhatsApp:

**1. Send the URL to the chat**
```
https://youtu.be/owmJyKVu5f8
```

**2. Hermes captures the transcript automatically**
```bash
python3 src/fetch_transcript.py 'https://youtu.be/owmJyKVu5f8' \
  --text-only --timestamps > /tmp/transcript_owmJyKVu5f8.txt
```

For Twitter/X, the pipeline uses `yt-dlp` to download the audio and `mlx-whisper` to transcribe locally on Apple Silicon.

**3. Claude translates and organizes**
The agent reads the transcript and produces a clean `.txt` in Brazilian Portuguese, split into thematic sections, with no timestamps, ads or spoken-language filler.

**4. HTML is generated**
```bash
python3 src/build_html.py \
  owmJyKVu5f8 \
  'Article title' \
  'Source / Channel' \
  'https://youtu.be/owmJyKVu5f8' \
  /tmp/owmJyKVu5f8_pt.txt \
  docs/posts/pt_br/article-slug.html
```

**5. Card is added to the index**
The agent edits `docs/index.html`, inserting the new card with title, description and link.

**6. Commit and push**
```bash
git add docs/posts/pt_br/article-slug.html index.html
git commit -m 'feat: adds article — Video title'
git push
```

> See [CLAUDE.md](CLAUDE.md) for full project documentation.

---

## Markdown for Agents (Cloudflare Worker)

The site serves regular HTML for humans and **automatic Markdown** for AI agents performing *content negotiation* via `Accept: text/markdown`. Inspired by Cloudflare's [Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/) feature — which is only available on paid plans — this project implements the same idea using **Cloudflare Workers on the Free plan**.

### Why it matters

An article HTML on this site costs ~53,000 tokens for an agent to read (markup, nav, scripts, CSS). The Markdown version of the same content consumes **~13,000 tokens — 75% less**. Agents save context, cost and latency.

### How it works

```
Human (Accept: text/html)
  → Cloudflare edge → GitHub Pages → full HTML

Agent (Accept: text/markdown)
  → Cloudflare edge → Worker intercepts → fetch HTML → convert → Markdown
```

The Worker runs at Cloudflare's edge (~10ms latency), consumes the HTML from origin (GitHub Pages) and returns clean Markdown with YAML frontmatter containing metadata.

### Quick test

```bash
# Normal HTML (human)
curl -sI https://adhenawer.net/posts/original/head-claude-code-happens-after-coding-solved.html | grep -i content-type
# content-type: text/html; charset=utf-8

# Markdown (agent)
curl -s https://adhenawer.net/posts/original/head-claude-code-happens-after-coding-solved.html \
  -H "Accept: text/markdown" | head -15
# ---
# title: "The Head of Claude Code on What Happens After Coding Is Solved"
# author: "Lenny's Podcast with Boris Cherny ..."
# description: "..."
# source: "https://adhenawer.net/..."
# lang: en
# ---
#
# ## THE PROGRAMMER WHO NO LONGER WRITES CODE
#
# 100% of my code is written by Claude Code...
```

Worker response headers:

| Header | Value |
|---|---|
| `Content-Type` | `text/markdown; charset=utf-8` |
| `x-markdown-tokens` | Token estimate for the returned Markdown |
| `Vary` | `Accept` (for correct caching) |
| `Cache-Control` | `public, max-age=3600` |

### Technical implementation

Location: `workers/markdown-agent/`

```
workers/markdown-agent/
├── wrangler.toml       ← Worker routes and config
├── package.json
└── src/
    └── index.js        ← logic: detect Accept → fetch HTML → convert → return
```

**Registered routes** (`wrangler.toml`):

```toml
routes = [
  { pattern = "adhenawer.net/posts/*", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/en/*", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/leituras/*", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/index.html", zone_name = "adhenawer.net" },
  { pattern = "adhenawer.net/llms.txt", zone_name = "adhenawer.net" }
]
```

**Worker flow** (`src/index.js`, summary):

The HTML→Markdown conversion is done with pure regex (no external dependencies) because the project's HTMLs have predictable structure (`<article>` wrapping `<h2>`, `<p>`, `<section>`, `<figure class="slide-figure">`). This avoids Turndown/JSDOM, which don't run natively in the Workers runtime.

### Cost

**Zero.** Cloudflare Workers' Free plan offers **100,000 requests/day at no cost**. More than enough for a static site with moderate agent traffic.

### Deploy

```bash
cd workers/markdown-agent
npm install
npx wrangler login          # first time only
npx wrangler deploy
```

### References

- Cloudflare blog post: [Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/)
- Feature docs (paid): [developers.cloudflare.com/fundamentals/reference/markdown-for-agents](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/)

---

## Reading features

- **3 themes**: ☀️ Sepia (default, Kindle-style) · 🌤️ Light · 🌙 Dark
- **Per-device progress** — each device saves its own reading position
- **Auto-resume** — "continue where you left off" banner on reopen
- **Progress bar** and reading % pinned while scrolling
- **Clickable TOC** with all sections
- Mobile-responsive

---

## Articles

The full article index lives at [adhenawer.net](https://adhenawer.net/) (PT-BR) and [adhenawer.net/en/](https://adhenawer.net/en/) (English).
