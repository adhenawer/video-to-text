# CLAUDE.md — Projeto video-to-text

Site estático com artigos de podcasts e vídeos sobre IA traduzidos para português brasileiro. Zero dependências — HTML puro.

## Estrutura

```
video-to-text/
├── CLAUDE.md
├── README.md
├── .gitignore
├── docs/                     ← frontend estático (GitHub Pages serve daqui)
│   ├── index.html              ← índice com todos os artigos
│   ├── css/
│   │   └── style.css           ← CSS centralizado (temas, index, artigos)
│   ├── js/
│   │   └── reader.js           ← JS de leitura (tema, progresso, resume)
│   ├── img/                    ← slides extraídos de apresentações
│   ├── posts/pt_br/               ← artigos HTML individuais
│   ├── robots.txt              ← permite crawling, aponta para sitemap
│   ├── sitemap.xml             ← URLs para Google
│   └── llms.txt                ← índice para crawlers de LLMs
├── transcripts/                ← transcrições persistidas, organizadas por provider
│   ├── youtube/                  ← {video_id}.txt (EN) + {video_id}_pt.txt (PT-BR)
│   └── twitter/                  ← {tweet_id}.txt (EN) + {tweet_id}_pt.txt (PT-BR)
├── tests/                      ← testes unitários (pytest, TDD obrigatório)
├── requirements.txt            ← dependências Python (mlx, mlx-lm, yt-dlp, mlx-whisper, ...)
├── src/                        ← pacote Python principal
│   ├── __init__.py             ← marca como pacote
│   ├── __main__.py             ← entry point: python3 -m src
│   ├── pipeline.py             ← orquestrador: URL → HTML (detecta provider automaticamente)
│   ├── build_html.py           ← gera HTML com SEO, JSON-LD e HTML semântico
│   ├── extract_slides.py       ← extrai slides de vídeos via ffmpeg + OpenCV
│   ├── fetch_transcript.py     ← CLI standalone: captura transcrição do YouTube
│   ├── translate_local.py      ← traduz via Gemma 4 local (mlx-lm)
│   └── providers/              ← abstração multi-provider (YouTube, Twitter/X, ...)
│       ├── __init__.py         ← registry: detect_provider(url)
│       ├── youtube.py          ← YouTube: youtube-transcript-api
│       └── twitter.py          ← Twitter/X: yt-dlp + mlx-whisper
```

## Rodar localmente

```bash
cd ~/code/video-to-text
python3 -m http.server 8899 --bind 0.0.0.0
# http://localhost:8899
# Rede local (celular): http://<SEU-IP-LOCAL>:8899
```

## Adicionar novo artigo

> **REGRA OBRIGATÓRIA: todo post DEVE ter versões PT e EN.**
> O seletor de idioma (`PT`/`EN`) aparece em todas as páginas. Se uma versão faltar,
> o botão correspondente fica desabilitado — mas o `index.json` precisa ter
> tanto `slug` (PT) quanto `slug_en`, e os arquivos devem existir em
> `docs/posts/pt_br/<slug>.html` **e** `docs/posts/original/<slug_en>.html`.
> Sem isso, há risco de hreflang quebrado e 404 na troca de idioma.
>
> Checklist por post:
> 1. `transcripts/{provider}/{id}.txt` — transcrição original (gerada pelo pipeline)
> 2. `transcripts/{provider}/{id}_pt.txt` — versão PT-BR formatada
> 3. `transcripts/{provider}/{id}_en.txt` — versão EN formatada (mesmo formato de seções)
> 4. `docs/posts/pt_br/<slug>.html` — gerado por `build_html.py` com `lang="pt_br"`
> 5. `docs/posts/original/<slug_en>.html` — gerado por `build_html.py` com `lang="original"`
> 6. Entrada em `transcripts/index.json` com **ambos** `slug` e `slug_en`
> 7. Cards adicionados em `docs/index.html` (PT) **e** `docs/en/index.html` (EN)

### Pipeline — YouTube (Claude traduz)

```bash
python3 src/pipeline.py \
  'https://youtu.be/VIDEO_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

### Pipeline — Twitter/X (Claude traduz)

```bash
python3 src/pipeline.py \
  'https://x.com/user/status/TWEET_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

### Pipeline — Twitter/X com extração de slides

```bash
python3 src/pipeline.py \
  'https://x.com/user/status/TWEET_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo' \
  --slides
```

Com `--slides`, o pipeline baixa o vídeo completo, extrai screenshots de cada slide distinto
(via ffmpeg + OpenCV), correlaciona com o texto por timestamp, e gera HTML com `<figure>` intercalados.
Imagens salvas em `img/{slug}/slide-NNNN.jpg`. Use `--scene-threshold 0.99` para mais slides.

O pipeline detecta automaticamente o provider pela URL.
- **YouTube**: captura legendas via `youtube-transcript-api`
- **Twitter/X**: baixa áudio via `yt-dlp`, transcreve via `mlx-whisper` (local, Apple Silicon)

Aguarda a tradução via Claude/Hermes e gera o HTML.
O Claude lê `/tmp/transcript_ID.txt` e salva a tradução em `/tmp/ID_pt.txt`.

### Pipeline (local — modelo open source)

```bash
python3 src/pipeline.py \
  'URL_DO_VIDEO' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo' \
  --local
```

Com `--local`, a tradução é feita por um LLM local via mlx-vlm (default: Gemma 4 E4B 8bit).
Para usar outro modelo: `--local --model mlx-community/outro-modelo`.

### Ou passo a passo

#### 1. Capturar transcrição

```bash
python3 src/fetch_transcript.py \
  'https://youtu.be/VIDEO_ID' --text-only --timestamps \
  2>/dev/null > /tmp/transcript_VIDEO_ID.txt
```

#### 2. Traduzir

**Via Claude (default):** Pedir ao Claude para ler `/tmp/transcript_VIDEO_ID.txt` e produzir **dois** `.txt`:
- **PT-BR:** português brasileiro natural, salvar em `/tmp/VIDEO_ID_pt.txt`
- **EN:** inglês formatado (mesmo formato de seções), salvar em `/tmp/VIDEO_ID_en.txt`

Ambos sem timestamps, sem `[music]`, sem propagandas, sem filler words.

**Via modelo local (PT):** `python3 src/translate_local.py /tmp/transcript_VIDEO_ID.txt /tmp/VIDEO_ID_pt.txt`

O output (de ambos) é um `.txt` com seções no formato:
```
================================================================================
[12:34] NOME DA SEÇÃO EM MAIÚSCULO

Parágrafo do conteúdo...
```

**`[mm:ss]` (ou `[hh:mm:ss]`) é obrigatório no início de cada título de seção** — marca o momento no vídeo onde aquele assunto começa. O `build_html.py` converte isso em link clicável (YouTube → `?t=N`) ou marcador de texto (Twitter, sem deep-link). Use o timestamp do primeiro segmento da transcrição original que pertence à seção. Sem o `[mm:ss]` o post ainda funciona (backward compat), mas perde o seek.

#### 3. Gerar HTML (PT **e** EN)

```bash
# PT-BR
python3 src/build_html.py \
  VIDEO_ID \
  'Título do Artigo' \
  'Subtítulo / Fonte' \
  'https://youtu.be/VIDEO_ID' \
  /tmp/VIDEO_ID_pt.txt \
  docs/posts/pt_br/slug-do-titulo.html

# EN (obrigatório — não pular)
python3 src/build_html.py \
  VIDEO_ID \
  'English Title' \
  'Author / Source' \
  'https://youtu.be/VIDEO_ID' \
  /tmp/VIDEO_ID_en.txt \
  docs/posts/original/english-slug.html
```

Salve também as transcrições formatadas em `transcripts/{provider}/{VIDEO_ID}_pt.txt` e `{VIDEO_ID}_en.txt` para reuso por `scripts/regen_en_htmls.py`.

#### 4. Atualizar `transcripts/index.json`

A entrada DEVE conter `slug` (PT) e `slug_en` (EN). Sem `slug_en`, o `build_html.py` não emite o link `hreflang="en"` e o botão EN fica desabilitado.

```json
{
  "video_id": "VIDEO_ID",
  "provider": "youtube",
  "title": "Título do Artigo",
  "subtitle": "Fonte / Canal",
  "url": "https://youtu.be/VIDEO_ID",
  "slug": "slug-do-titulo",
  "slug_en": "english-slug",
  "date": "YYYY-MM-DD"
}
```

### 5. Adicionar card nos índices (PT **e** EN)

Inserir novo `<a class="card">` em `docs/index.html` (PT) **e** `docs/en/index.html` (EN) com:
- `href="posts/pt_br/slug-do-titulo.html"` (PT) / `href="posts/original/english-slug.html"` (EN)
- Título, meta (fonte, autor), descrição resumida
- `<div class="progress-info" id="p-VIDEOID"></div>`
- No `<script>` de cada index, adicionar: `showProgress('reading_VIDEO_ID_', 'p-VIDEOID');`

> **Não** adicionar `<div class="tags">` manualmente. As pílulas `#tag` são
> injetadas em runtime por `docs/js/tags.js`, que lê `tags`/`category` de
> `data/moc.json`.

### 6. Atribuir tags e regenerar grafo + JSON-LD

Toda nova entrada em `transcripts/index.json` precisa de **tags** (array) e
**category** (`"core"` ou `"lateral"`). O mapeamento é versionado em
`scripts/apply_tags.py` (single source of truth). Fluxo:

```bash
# 1. Editar TAG_MAP em scripts/apply_tags.py — incluir o novo slug
# 2. Aplicar mapping ao index.json
python3 scripts/apply_tags.py
# 3. Regenerar moc.json + injetar JSON-LD inline em moc.html e índices
python3 scripts/build_moc.py
```

**Tags disponíveis:** `claude-code`, `agentic-engineering`, `carreira`,
`soft-skills`, `produto`, `tutoriais`, `ia-2026`, `financas`. Use 1–4 por post.

**Categorias:**
- `core` — espinha dorsal do site (AI, produto, carreira, agentes)
- `lateral` — outliers (finanças, trading, mercado, lateral pessoal). Cards
  `lateral` são movidos pelo `tags.js` para a seção **"Curiosidades"** no fim
  do índice, separadas do fluxo principal.

**Como funciona:**
- `docs/js/tags.js` lê `data/moc.json` no client; injeta `<div class="tags">`
  em cada card, monta a `tag-bar` no topo e move `lateral` pro fim. Suporta
  deep-link via `?#tag-claude-code`.
- `scripts/build_moc.py` injeta automaticamente um bloco
  `<script type="application/ld+json">` (Dataset + Articles + Action edges)
  em `docs/moc.html`, `docs/index.html` e `docs/en/index.html` para que
  crawlers de IA leiam o grafo sem JS. O bloco é delimitado por
  `<!-- MOC-LD:BEGIN ... -->` / `<!-- MOC-LD:END -->` e re-escrito a cada run.

**Posts órfãos** (HTML existe mas não há entrada em `index.json`, ex.
`ronycoder-video.html`, `dario-amodei-...`): adicionar fallback no dict
`ORPHAN_TAGS` dentro de `docs/js/tags.js`. Ideal é regularizar criando
entrada no `index.json`.

### 7. Commit

```bash
git add docs/posts/pt_br/slug-do-titulo.html \
        docs/posts/original/english-slug.html \
        docs/index.html docs/en/index.html \
        transcripts/
git commit -m 'feat: adiciona artigo — Título do Vídeo'
```

## Scripts

| Script | Uso |
|--------|-----|
| `src/pipeline.py` | Orquestrador: URL → HTML. Detecta provider automaticamente (YouTube, Twitter/X) |
| `src/providers/` | Abstração multi-provider. Cada provider implementa `detect()`, `extract_id()`, `fetch_transcript()` |
| `src/extract_slides.py` | Extrai slides de vídeos via ffmpeg (amostragem) + OpenCV (detecção de mudanças) |
| `src/fetch_transcript.py` | CLI standalone: captura transcrição do YouTube via `youtube-transcript-api` |
| `src/translate_local.py` | Traduz transcrição para PT-BR via LLM local (`mlx-vlm`). Usado com `--local` |
| `src/build_html.py` | Gera HTML referenciando `../css/style.css` e `../js/reader.js` |
| `scripts/apply_tags.py` | Aplica `tags`+`category` em `transcripts/index.json` (TAG_MAP é source of truth) |
| `scripts/build_moc.py` | Gera `docs/data/moc.json` + injeta JSON-LD inline em `moc.html` e índices |
| `scripts/regen_en_htmls.py` | Regenera todos os HTMLs EN com sidebar de referências |
| `scripts/patch_ptbr_references.py` | Injeta sidebar de referências nos HTMLs PT-BR existentes |
| `scripts/update_index_references.py` | Atualiza contagens de refs em `transcripts/index.json` |

## Arquivos compartilhados

| Arquivo | Papel |
|---------|-------|
| `css/style.css` | CSS centralizado: temas (sépia/claro/escuro), classes `.page-index` e `.page-article`, `.tag` e `.tag-bar` |
| `js/reader.js` | JS de leitura: tema, barra de progresso, salvar posição, resume banner. Lê `data-storage-key` do `<body>` |
| `js/tags.js` | Injeta pílulas `#tag` clicáveis em cada card do índice, monta a barra de filtros e move `category=lateral` para a seção "Curiosidades" no fim |
| `js/lang.js` | Seletor de idioma PT/EN, redireciona usando `slug`/`slug_en` |
| `data/moc.json` | Grafo dos artigos: `nodes` (com `tags`+`category`) e `edges` (related_posts). Consumido por `moc.html` e `tags.js` |

Artigos usam `<body class="page-article" data-storage-key="reading_VIDEO_ID_">`.
Index usa `<body class="page-index">`.

### Setup (uma vez)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Isso instala: `mlx`, `mlx-lm`, `mlx-vlm`, `youtube-transcript-api`, `yt-dlp` e `mlx-whisper`.

Para usar `--local`, o modelo de tradução é baixado automaticamente na primeira execução.
Default local: `mlx-community/gemma-4-e4b-it-8bit` (~8GB, M1 Pro 16GB no limite).
Ver `benchmarks/` para comparativo de qualidade entre modelos.

Para Twitter/X, o modelo Whisper (`mlx-community/whisper-large-v3-turbo`, ~1.5GB) é baixado na primeira execução.

## Design System

### Temas (3 opções via botões)

| Tema | BG | Texto | Accent |
|------|----|-------|--------|
| ☀️ Sépia (padrão) | `#FAF4E8` | `#3D3529` | `#C17C3E` |
| 🌤️ Claro | `#F0F2F5` | `#2D3748` | `#E07850` |
| 🌙 Escuro | `#1E1E24` | `#D4D0C8` | `#C4956A` |

**Por que sépia?** Branco puro (`#FFF`) causa halation (efeito fantasma) em astigmatismo (~50% da população). Sépia estilo Kindle é o padrão mais confortável para leitura longa. Nunca usar preto puro nem branco puro.

### Tipografia
- Corpo: Georgia (serif), 1.08em, line-height 1.7
- UI (nav, botões, meta): -apple-system sans-serif
- Letter-spacing: 0.01em no body

### Gerenciamento de sessão de leitura
- `_deviceId` no localStorage identifica o dispositivo
- Posição salva em `reading_VIDEO_ID_DEVICEID`: scrollY, scrollPct, section, sectionTitle, theme
- Ao reabrir: banner "Continuar de onde parou" por 8.5s
- Tema salvo separadamente em `_reading_theme`

### STORAGE_KEY por artigo
```
boris_cherny       → reading_boris_
simon_willison     → reading_
outros             → reading_VIDEO_ID_
```

## SEO

Cada artigo HTML inclui meta tags para indexação e compartilhamento:

- `<meta name="description">` — primeiro parágrafo do artigo (até 200 chars)
- `<meta property="og:title/description/locale/site_name">` — Open Graph (WhatsApp, LinkedIn, Facebook)
- `<meta name="twitter:card/title/description">` — Twitter Card
- `<meta name="author">` — subtitle do artigo

Gerados automaticamente pelo `build_html.py` a partir do conteúdo traduzido.

Arquivos de SEO no root:
- `robots.txt` — permite crawling, aponta para sitemap
- `sitemap.xml` — lista todas as URLs de artigos (atualizar ao adicionar novo artigo)

### LLMO (Otimização para LLMs)

O `build_html.py` gera automaticamente:
- **JSON-LD** (schema.org `Article`) — headline, description, author, sections, inLanguage
- **HTML semântico** — `<article>`, `<section>`, `<nav aria-label>`, `<cite>`, `<figure>`
- **Parágrafos auto-contidos** — cada parágrafo faz sentido sozinho (citável por LLMs)
- **`rel="noopener"`** em links externos

Arquivo `llms.txt` no root — convenção para crawlers de LLMs (similar a robots.txt):
- Lista todos os artigos com título, fonte, seções e resumo
- Atualizar ao adicionar novo artigo

### Atualizar sitemap ao adicionar artigo

Após adicionar um novo artigo, atualizar `sitemap.xml` adicionando:
```xml
<url>
  <loc>https://adhenawer.net/posts/pt_br/SLUG.html</loc>
  <lastmod>YYYY-MM-DD</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
```

## Referências (sidebar fixa)

Cada artigo tem uma sidebar fixa com referências extraídas da transcrição original: livros (Amazon search), ferramentas (site oficial), papers (arXiv), pessoas (**Twitter prioritário**), conceitos (Wikipedia), empresas e **posts relacionados** dentro do próprio site.

### Regra de prioridade para `people`

**Ordem preferencial do campo `url`:**
1. **Twitter/X** (`https://twitter.com/handle` ou `https://x.com/handle`) — PRIMEIRA ESCOLHA. Tente descobrir o handle:
   - Buscando no perfil do LinkedIn/Wikipedia/blog pessoal se a pessoa linka o Twitter lá
   - Inferindo handles óbvios quando a pessoa é conhecida (ex: Simon Willison → `simonw`, Boris Cherny → `bcherny`)
   - Usando o handle mencionado na própria transcrição se houver
2. LinkedIn se for figura executiva/corporativa e sem Twitter público
3. Site pessoal / blog oficial (colah.github.io, simonwillison.net, etc.)
4. Wikipedia apenas como fallback final

Nunca invente um handle Twitter; se não conseguir confirmar, use o próximo tier da lista.

### Arquivos

- `transcripts/{provider}/{video_id}.references.json` — JSON estruturado por post
- `transcripts/index.json` — inclui campo `references.counts` e `.total` por entrada

### Schema JSON

```json
{
  "video_id": "...",
  "extracted_at": "YYYY-MM-DD",
  "books": [{"title":"...","author":"...","url":"amazon.com/s?k=...","context":"..."}],
  "tools": [{"name":"...","url":"...","context":"..."}],
  "papers": [{"title":"...","authors":"...","url":"arxiv.org/...","context":"..."}],
  "people": [{"name":"...","role":"...","url":"...","context":"..."}],
  "concepts": [{"name":"...","url":"en.wikipedia.org/...","context":"..."}],
  "companies": [{"name":"...","url":"..."}],
  "related_posts": [{"slug_pt":"...","slug_en":"...","reason":"..."}]
}
```

### Extrair referências de um novo artigo

Peça ao Claude Code:
```
> extrai referências de transcripts/{provider}/{video_id}.txt seguindo o schema em CLAUDE.md
> (use a transcrição no idioma original)
> escreva em transcripts/{provider}/{video_id}.references.json
```

### Regenerar HTMLs após extrair

```bash
# EN — build_html.py carrega refs automaticamente via provider
python3 scripts/regen_en_htmls.py

# PT-BR — patcher injeta a sidebar renderizada
python3 scripts/patch_ptbr_references.py

# Atualiza contagens no index.json
python3 scripts/update_index_references.py

# Regenera o mapa de conteúdo + JSON-LD inline em moc.html, index PT/EN
# (consome tags/category do transcripts/index.json — rode apply_tags.py antes
# se acabou de adicionar entrada nova)
python3 scripts/build_moc.py
```

### Renderização

- `src/build_html.py` → `_render_references_sidebar(refs, is_ptbr)` gera o `<aside class="references-sidebar">`
- `build_html.make_html(..., provider=...)` — com o parâmetro `provider`, carrega automaticamente o JSON e injeta a sidebar
- CSS: `.references-sidebar` em `docs/css/style.css` (fixa à direita em telas ≥1200px, inline no final do artigo em telas menores)

---

## Analytics (Umami)

**TODO HTML novo ou manualmente criado DEVE incluir o snippet do Umami dentro de `<head>`:**

```html
<script defer src="https://cloud.umami.is/script.js" data-website-id="40c8ae3d-2e6b-4af4-a89b-f578dd3b2315"></script>
```

O `build_html.py` já inclui automaticamente. Para HTMLs criados manualmente (blog, landing pages, etc.), inserir o snippet imediatamente antes de `</head>`.

Se esquecer e criar vários de uma vez, rodar:
```bash
python3 scripts/inject_umami.py
```
Esse script injeta o snippet em todos os `.html` em `docs/` que ainda não o têm.

Dashboard: https://cloud.umami.is — site "adhenawer.net" (ID: `40c8ae3d-2e6b-4af4-a89b-f578dd3b2315`).

---

## Testes (TDD obrigatório)

Toda nova implementação DEVE seguir TDD:

1. **RED** — escreva o teste primeiro, rode `pytest`, veja falhar
2. **GREEN** — implemente o mínimo para o teste passar
3. **REFACTOR** — limpe o código mantendo testes verdes

```bash
# Rodar todos os testes
python3 -m pytest tests/ -v

# Rodar um módulo específico
python3 -m pytest tests/test_providers.py -v

# Rodar um teste específico
python3 -m pytest tests/test_build_html.py::TestJsonLd::test_jsonld_headline -v
```

### Estrutura de testes

```
tests/
├── __init__.py
├── conftest.py              ← fixtures compartilhadas (tmp_dir, sample_translated_txt, etc.)
├── test_providers.py        ← providers: detect, extract_id, timestamps, registry
├── test_build_html.py       ← HTML: estrutura, SEO, JSON-LD, semântica, slides, TOC
├── test_extract_slides.py   ← slides: timestamps, JSON, matching
└── test_pipeline.py         ← pipeline: detecção de provider, interface
```

### Regras

- Novos providers DEVEM ter testes de `detect()` e `extract_id()` com URLs válidas e inválidas
- Novas features no `build_html.py` DEVEM ter teste verificando o HTML gerado
- Funções utilitárias (formatação, parsing) DEVEM ter testes de edge cases
- Usar fixtures do `conftest.py` para dados de teste (não criar arquivos manualmente)

## Convenções

- Slugs: kebab-case PT-BR sem acentos → `como-construi-sistema-suporte-cliente-ia.html`
- Traduções `.txt`: ficam em `/tmp`, não commitadas (`.gitignore` ignora `*.txt`)
- Commits: `feat: adiciona artigo — Título` / `fix: ...` / `style: ...` / `docs: ...`

## Subir no GitHub

```bash
cd ~/code/video-to-text
gh repo create video-to-text --public --source=. --remote=origin
git push -u origin main
```

Ou via HTTPS:
```bash
git remote add origin https://github.com/<SEU-USUARIO>/video-to-text.git
git push -u origin main
```

Para GitHub Pages (deploy automático):
```bash
gh repo edit --enable-pages --branch main --dir /
```
Site ficará em: `https://<SEU-USUARIO>.github.io/video-to-text`

## Cloudflare Worker (redirects + markdown edge)

O Worker em `workers/markdown-agent/` fica na frente do GitHub Pages e intercepta as rotas declaradas em `wrangler.toml` (`/blog/*`, `/posts/*`, `/en/*`, `/leituras/*`, `/index.html`, `/llms.txt`). Responsabilidades:

- Serve HTML normal para navegadores
- Serve Markdown automaticamente para crawlers de IA (`autoDetectAiCrawlers`)
- Aplica os redirects definidos em `src/index.ts` — **HTTP 301 real** (não meta refresh)

### Configurar redirects

Editar `workers/markdown-agent/src/index.ts`, campo `redirects`:

```ts
redirects: {
  "/path-antigo/*": "/path-novo/$1",         // wildcard com backreference
  "/post-antigo.html": "/post-novo.html",    // literal (match exato)
}
```

Ambas as formas retornam 301. Wildcard é útil pra renomear uma árvore inteira; literal pra um post específico.

### Deploy

Pré-requisito (uma vez por máquina) — login no Cloudflare via OAuth no browser:

```bash
cd workers/markdown-agent
./node_modules/.bin/wrangler login
```

Depois, para publicar:

```bash
cd workers/markdown-agent
./node_modules/.bin/wrangler deploy
```

> `npx wrangler` pode falhar em ambientes com proxies/rewrites de CLI — prefira `./node_modules/.bin/wrangler` direto.

### Validar após deploy

```bash
# 301 em redirect configurado
curl -sI https://adhenawer.net/<path-antigo> | head -5
# esperado: HTTP/2 301 + location: <path-novo>

# Markdown para agentes
curl -s -H "Accept: text/markdown" https://adhenawer.net/blog/<slug>.html | head -20
# esperado: frontmatter YAML + corpo em Markdown
```

### Reindexação no Google após mudar slug

1. Configurar o redirect 301 no worker + deploy
2. (Opcional) Google Search Console → Inspect URL na URL **nova** → "Request indexing" pra acelerar
3. URL antiga sai do índice naturalmente quando o crawler do Google passar e receber o 301
