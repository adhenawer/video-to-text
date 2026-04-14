# video-to-text

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/adhenawer/video-to-text)](https://github.com/adhenawer/video-to-text/releases)
[![Live demo](https://img.shields.io/badge/demo-adhenawer.net-C17C3E)](https://adhenawer.net/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-MLX-black)](https://github.com/ml-explore/mlx)
[![Cloudflare Workers](https://img.shields.io/badge/edge-Cloudflare%20Workers-F38020)](https://workers.cloudflare.com/)

> 🇧🇷 **[Leia em português brasileiro](README-pt_br.md)** · 🇺🇸 You are reading in English

Turns YouTube and Twitter/X videos and podcasts into readable posts — organized by sections and published as static HTML.

<p align="center">
  <img src="docs/img/hero.svg" alt="URL → transcription → translation → bilingual article" width="820">
</p>

---

## Why

Long-form video is hard to skim, quote, search, or reread. This project turns videos into structured articles you can actually read.

- **Local transcription** via Whisper — no API cost for audio
- **LLM-organized** into thematic sections — not a chronological wall of text
- **Bilingual** out of the box — PT-BR and English with `hreflang` alternates
- **Agent-friendly** — Cloudflare Worker on free tier serves Markdown to AI crawlers via content negotiation (75% fewer tokens than HTML)
- **Zero frontend build** — static HTML deployable to GitHub Pages

Live at [adhenawer.net](https://adhenawer.net/) · [Blog](https://adhenawer.net/blog/)

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

> **Note on agents**: this project used to run inside external agents (OpenCode/Hermes) sending the pipeline over WhatsApp. Anthropic has since blocked subscription tokens from being reused by third-party agents, so the workflow now runs **directly inside [Claude Code](https://claude.com/claude-code)** — the official Anthropic CLI. You drive the pipeline by chatting with Claude Code in your terminal; it edits files, runs commands and pushes to git on your behalf.

### 1. Install Claude Code

```bash
# macOS / Linux / WSL2
curl -fsSL https://claude.ai/install.sh | bash

# Alternatively, via npm (any OS)
npm install -g @anthropic-ai/claude-code
```

Run `claude` in any directory to start the agent. First run will prompt you to sign in with your Anthropic account (subscription or API key).

### 2. Clone and install Python deps

```bash
git clone https://github.com/adhenawer/video-to-text
cd video-to-text
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` includes `youtube-transcript-api`, `yt-dlp`, `mlx-whisper`, `mlx-vlm` and others.

### 3. Install Whisper (Apple Silicon)

Whisper runs **locally** — no API calls, no external cost. This project uses [`mlx-whisper`](https://github.com/ml-explore/mlx-examples/tree/main/whisper), the MLX framework natively optimized for Apple Silicon (M1/M2/M3/M4).

```bash
# ffmpeg is needed by yt-dlp to demux audio
brew install ffmpeg

# mlx-whisper already installed via requirements.txt
# Model (~1.5GB) is auto-downloaded on first run:
#   mlx-community/whisper-large-v3-turbo
```

Recommended hardware: M1 Pro 16GB or higher. Transcription runs at ~5× real-time speed.

### 4. Run the local server

```bash
python3 -m http.server 8080
# http://localhost:8080
# Local network (phone): http://<YOUR-LOCAL-IP>:8080
```

---

## Detailed agentic flow (inside Claude Code)

This is the exact flow I use daily. You open the project in Claude Code (`claude` in the repo root) and drive everything through chat.

### macOS example

**1. Start Claude Code in the repo**

```bash
cd ~/code/video-to-text
claude
```

**2. Ask Claude Code to process a video**

```
> add article from https://youtu.be/owmJyKVu5f8
```

Claude Code then, on its own:

- Runs `python3 src/fetch_transcript.py 'https://youtu.be/owmJyKVu5f8' --text-only --timestamps > /tmp/transcript_owmJyKVu5f8.txt`
- Reads the transcript, translates to PT-BR and organizes into thematic sections, writing `/tmp/owmJyKVu5f8_pt.txt`
- Calls `python3 src/build_html.py owmJyKVu5f8 'Title' 'Source' 'URL' /tmp/owmJyKVu5f8_pt.txt docs/posts/pt_br/SLUG.html`
- Edits `docs/index.html` to add a card
- Updates `docs/sitemap.xml` and `docs/llms.txt`
- `git add`, `git commit`, `git push`

You review the diff inside Claude Code. If anything looks off, ask it to fix.

### Twitter/X flow

```
> transcribe https://x.com/user/status/1234567890
```

Under the hood:

- `yt-dlp` downloads the audio to `/tmp/`
- `mlx-whisper` transcribes locally on Apple Silicon
- Same translation + HTML generation path as YouTube

### Full project docs

> See [CLAUDE.md](CLAUDE.md) for the full project knowledge base Claude Code uses to navigate the codebase.

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

## References sidebar

Each article has a fixed sidebar (right side on wide screens, inline on mobile) with references extracted from the **original-language transcript** via LLM subagents. Categories:

| Category | Icon | Link target |
|---|---|---|
| Books | 📖 | Amazon search (`amazon.com/s?k=...`) |
| Tools | 🛠 | Canonical product site |
| Papers | 📄 | arXiv / author's blog |
| People | 👥 | **Twitter/X preferred**, fallback to LinkedIn / personal site / Wikipedia |
| Concepts | 🧠 | Wikipedia / transformer-circuits.pub |
| Companies | 🏢 | Official site |
| Related posts | 🔗 | Internal cross-link (to the other language's canonical slug) |

### How extraction works

1. **Source of truth**: the raw transcript in its original language (`transcripts/{provider}/{id}.txt`)
2. **Subagents** (one per post, run in parallel) receive the transcript plus the schema and available slug mappings
3. Each subagent writes `transcripts/{provider}/{id}.references.json` — the **persisted subproduct**
4. `transcripts/index.json` gets a summary per entry: `references.counts.*` and `references.total`
5. `build_html.py` loads the JSON automatically when `provider=...` is passed and renders the sidebar

### JSON schema

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

### People priority: Twitter first

The `people[]` URL field follows a strict order: **Twitter/X handle first**, then LinkedIn, then personal site/blog, and Wikipedia only as last resort. The extraction subagents try to derive the handle from the person's public profile. For historical figures or deceased academics who never had Twitter, the field is left empty or points to Wikipedia.

Enrichment is idempotent: running `scripts/enrich_people_twitter.py` applies a curated handle table across all references JSONs without overwriting existing Twitter URLs.

### Stats as of v2

- **714 references** extracted across 21 posts
- Richest: *State of AI 2026* (Simon Willison, 61 refs) · *From IDEs to AI Agents* (Steve Yegge, 59) · *Behavioral Finance* (Shiller, 55)
- Extracted in parallel by 20 subagents in ~2 minutes

### Adding references to a new article

Inside Claude Code:

```
> extract references from transcripts/youtube/{ID}.txt following the schema in CLAUDE.md
> write to transcripts/youtube/{ID}.references.json
```

Then:

```bash
python3 scripts/regen_en_htmls.py         # rebuilds EN HTMLs with sidebar
python3 scripts/patch_ptbr_references.py  # injects sidebar into existing PT-BR HTMLs
python3 scripts/update_index_references.py  # refreshes counts in index.json
```

---

## Articles

The full article index lives at [adhenawer.net](https://adhenawer.net/) (PT-BR) and [adhenawer.net/en/](https://adhenawer.net/en/) (English).
