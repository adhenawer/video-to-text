# video-to-text

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/adhenawer/video-to-text)](https://github.com/adhenawer/video-to-text/releases)
[![GitHub Pages](https://img.shields.io/badge/demo-GitHub%20Pages-blue)](https://adhenawer.net/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-MLX-black)](https://github.com/ml-explore/mlx)

Transforma vídeos e podcasts do YouTube e Twitter/X em artigos de leitura — traduzidos para português brasileiro, organizados por seções e publicados como HTML estático.

## Por que criei o projeto 

Eu prefiro ler um post do que assistir um vídeo longo. Leio no meu ritmo, pulo o que não interessa, volto no que precisa de mais atenção.

O que me motivou foi acompanhar as tendências de IA, o volume de conteúdo em podcasts e vídeos é enorme. Não tenho tempo de assistir, a solução foi automatizar: mando o link de um vídeo pelo WhatsApp para o [Hermes](https://github.com/NousResearch/hermes-agent) e ele devolve o artigo pronto, traduzido e organizado em seções.

A ideia é consumir o conteúdo pelo celular, então o formato importa. Cada artigo é um post limpo, dividido em seções com índice clicável, progresso salvo e retomada automática. As cores seguem a paleta sépia de e-readers como o Kindle — conforto para leitura longa, sem cansar a vista.

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
| Frontend | HTML estático — zero frameworks, zero build steps |
| Hosting | GitHub Pages ou qualquer servidor estático |

---

## Setup completo

### 1. Instalar o Hermes

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/src/install.sh | bash
source ~/.bashrc   # ou: source ~/.zshrc
hermes             # inicia o agente no terminal
```

Funciona em Linux, macOS e WSL2. O instalador cuida de Python, Node.js e dependências.

### 2. Configurar modelo e ferramentas

```bash
hermes model    # escolhe o provider e modelo (ex: anthropic:claude-sonnet-4-6)
hermes tools    # habilita as ferramentas necessárias
```

Para usar Claude, você precisa de uma chave da Anthropic em `ANTHROPIC_API_KEY`.

### 3. Conectar ao WhatsApp (opcional, mas recomendado)

O Hermes pode receber mensagens direto do WhatsApp. Para configurar:

```bash
hermes gateway setup    # configura as plataformas de mensagens
hermes gateway start    # inicia o gateway
```

Escaneie o QR code com o WhatsApp. Depois de conectado, você envia URLs direto pelo app e recebe o artigo gerado.

> Também funciona via Telegram, Discord, Slack ou direto no terminal com `hermes`.

### 4. Clonar este repositório

```bash
git clone https://github.com/<SEU-USUARIO>/video-to-text
cd video-to-text
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Rodar o servidor local

```bash
python3 -m http.server 8080
# http://localhost:8080
# Rede local (celular): http://<SEU-IP-LOCAL>:8080
```

---

## Uso via pipeline

### YouTube (Claude traduz)

```bash
python3 src/pipeline.py \
  'https://youtu.be/VIDEO_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

### Twitter/X (Claude traduz)

```bash
python3 src/pipeline.py \
  'https://x.com/user/status/TWEET_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

### Tradução local (Gemma 4)

```bash
python3 src/pipeline.py \
  'URL_DO_VIDEO' \
  --title 'Título' --subtitle 'Fonte' --slug 'slug' \
  --local
```

O pipeline detecta o provider automaticamente pela URL.

---

## Fluxo agêntico detalhado

Este é o fluxo exato que uso no dia a dia via WhatsApp:

**1. Envio a URL no chat**
```
https://youtu.be/owmJyKVu5f8
```

**2. O Hermes captura a transcrição automaticamente**
```bash
python3 src/fetch_transcript.py 'https://youtu.be/owmJyKVu5f8' \
  --text-only --timestamps > /tmp/transcript_owmJyKVu5f8.txt
```

Para Twitter/X, o pipeline usa `yt-dlp` para baixar o áudio e `mlx-whisper` para transcrever localmente no Apple Silicon.

**3. Claude traduz e organiza**
O agente lê a transcrição e produz um `.txt` limpo em português brasileiro, dividido em seções temáticas, sem timestamps, propagandas ou vícios de linguagem oral.

**4. O HTML é gerado**
```bash
python3 src/build_html.py \
  owmJyKVu5f8 \
  'Título do Artigo' \
  'Fonte / Canal' \
  'https://youtu.be/owmJyKVu5f8' \
  /tmp/owmJyKVu5f8_pt.txt \
  docs/posts/pt_br/slug-do-titulo.html
```

**5. O card é adicionado ao índice**
O agente edita `docs/index.html` inserindo o novo card com título, descrição e link.

**6. Commit e push**
```bash
git add docs/posts/pt_br/slug-do-titulo.html index.html
git commit -m 'feat: adiciona artigo — Título do Vídeo'
git push
```

> Ver [CLAUDE.md](CLAUDE.md) para documentação completa do projeto.

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

```js
export default {
  async fetch(request) {
    // 1. Redirect 301 de URLs legadas /leituras/ → /posts/pt_br/
    const url = new URL(request.url);
    if (url.pathname.startsWith("/leituras/")) {
      return Response.redirect(
        url.origin + url.pathname.replace("/leituras/", "/posts/pt_br/"),
        301
      );
    }

    // 2. Se não pediu Markdown, passa HTML direto
    const accept = request.headers.get("Accept") || "";
    if (!accept.includes("text/markdown")) {
      return fetch(request);
    }

    // 3. Busca HTML do origin
    const response = await fetch(new Request(request.url, {
      headers: { Accept: "text/html" }
    }));
    const html = await response.text();

    // 4. Extrai <article>, converte para Markdown via regex
    const articleHtml = html.match(/<article[^>]*>([\s\S]*?)<\/article>/i)?.[1];
    const markdown = htmlToMarkdown(articleHtml);

    // 5. Monta frontmatter YAML + Markdown
    const final = [
      "---",
      `title: "${meta.title}"`,
      `author: "${meta.author}"`,
      `source: "${request.url}"`,
      "lang: pt-BR",
      "---",
      "",
      markdown
    ].join("\n");

    // 6. Retorna com headers corretos
    return new Response(final, {
      headers: {
        "Content-Type": "text/markdown; charset=utf-8",
        "x-markdown-tokens": String(Math.ceil(final.length / 4)),
        "Vary": "Accept",
        "Cache-Control": "public, max-age=3600",
      }
    });
  }
};
```

A conversão HTML→Markdown é feita com regex puro (sem dependências externas) porque os HTMLs do projeto têm estrutura previsível (`<article>` envolvendo `<h2>`, `<p>`, `<section>`, `<figure class="slide-figure">`). Evita Turndown/JSDOM que não rodam nativamente em Workers runtime.

### Custo

**Zero.** O plano Free do Cloudflare Workers oferece **100.000 requests/dia gratuitos**. Para um site estático com tráfego moderado de agentes, é mais do que suficiente.

### Deploy

```bash
cd workers/markdown-agent
npm install
npx wrangler login          # primeira vez
npx wrangler deploy
```

### Referências

- Blog post da Cloudflare: [Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/)
- Doc da feature (pago): [developers.cloudflare.com/fundamentals/reference/markdown-for-agents](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/)

---

## Features de leitura

- **3 temas**: ☀️ Sépia (padrão, estilo Kindle) · 🌤️ Claro · 🌙 Escuro
- **Progresso por dispositivo** — cada dispositivo salva a posição independentemente
- **Retomada automática** — banner "continuar de onde parou" ao reabrir
- **Barra de progresso** e % lido fixos durante a rolagem
- **Índice clicável** com todas as seções
- Responsivo para mobile

---

## Artigos

1. [Chefe do Claude Code: o que acontece depois que a programação for resolvida](https://adhenawer.net/posts/pt_br/chefe-do-claude-code-o-que-acontece-depois-que-a-programacao-for-resolvida.html)
2. [Estado da IA em 2026: ponto de inflexão — Simon Willison](https://adhenawer.net/posts/pt_br/estado-da-ia-2026-ponto-de-inflexao-simon-willison.html)
3. [Práticas de engenharia para agentes de código — Simon Willison](https://adhenawer.net/posts/pt_br/praticas-de-engenharia-para-agentes-de-codigo-simon-willison.html)
4. [De IDEs para Agentes de IA — Steve Yegge](https://adhenawer.net/posts/pt_br/de-ides-para-agentes-de-ia-steve-yegge.html)
5. [Engenheiro sênior: fluxo de desenvolvimento com especificações e IA](https://adhenawer.net/posts/pt_br/engenheiro-senior-fluxo-desenvolvimento-especificacoes-ia.html)
6. [Um agente não é suficiente: programação agêntica além do Claude Code](https://adhenawer.net/posts/pt_br/um-agente-nao-e-suficiente-programacao-agentica-alem-do-claude-code.html)
7. [Do prompt à produção: o que é engenharia agêntica](https://adhenawer.net/posts/pt_br/do-prompt-a-producao-o-que-e-engenharia-agentica.html)
8. [Engenharia agêntica: contexto, guardrails e criatividade](https://adhenawer.net/posts/pt_br/engenharia-agentica-contexto-guardrails-e-criatividade.html)
9. [Como construí um sistema de suporte ao cliente com IA de nível produção](https://adhenawer.net/posts/pt_br/como-construi-sistema-suporte-cliente-ia-nivel-producao.html)
10. [Fluxos de trabalho agênticos — Don Syme](https://adhenawer.net/posts/pt_br/fluxos-de-trabalho-agenticos-don-syme.html)
11. [Roteiro: engenheiro de IA para desenvolvedores de software](https://adhenawer.net/posts/pt_br/roteiro-engenheiro-ia-para-desenvolvedores-de-software.html)
12. [Política corporativa em tech — Ethan Evans (ex-VP Amazon)](https://adhenawer.net/posts/pt_br/politica-corporativa-tech-tudo-que-ninguem-te-conta.html)
13. [Por que paramos de construir agentes e começamos a construir skills — Anthropic](https://adhenawer.net/posts/pt_br/por-que-paramos-de-construir-agentes-e-comecamos-a-construir-skills.html) *(via Twitter/X)*
