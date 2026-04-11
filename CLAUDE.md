# CLAUDE.md — Projeto video-to-text

Site estático com artigos de podcasts e vídeos sobre IA traduzidos para português brasileiro. Zero dependências — HTML puro.

## Estrutura

```
video-to-text/
├── CLAUDE.md
├── README.md
├── .gitignore
├── index.html                  ← índice com todos os artigos (usa css/style.css)
├── css/
│   └── style.css               ← CSS centralizado (temas, index, artigos)
├── js/
│   └── reader.js               ← JS compartilhado de leitura (tema, progresso, resume)
├── requirements.txt            ← dependências Python (mlx, mlx-lm, yt-dlp, mlx-whisper, ...)
├── scripts/
│   ├── providers/              ← abstração multi-provider (YouTube, Twitter/X, ...)
│   │   ├── __init__.py         ← registry: detect_provider(url)
│   │   ├── youtube.py          ← YouTube: youtube-transcript-api
│   │   └── twitter.py          ← Twitter/X: yt-dlp + mlx-whisper
│   ├── fetch_transcript.py     ← CLI standalone: captura transcrição do YouTube
│   ├── translate_local.py      ← traduz via Gemma 4 local (mlx-lm)
│   ├── build_html.py           ← gera HTML referenciando css/ e js/
│   └── pipeline.py             ← orquestrador: URL → HTML (detecta provider automaticamente)
└── leituras/                   ← artigos individuais (usam ../css/style.css + ../js/reader.js)
    ├── chefe-do-claude-code-o-que-acontece-depois-que-a-programacao-for-resolvida.html
    ├── estado-da-ia-2026-ponto-de-inflexao-simon-willison.html
    ├── praticas-de-engenharia-para-agentes-de-codigo-simon-willison.html
    ├── de-ides-para-agentes-de-ia-steve-yegge.html
    ├── engenheiro-senior-fluxo-desenvolvimento-especificacoes-ia.html
    ├── um-agente-nao-e-suficiente-programacao-agentica-alem-do-claude-code.html
    ├── do-prompt-a-producao-o-que-e-engenharia-agentica.html
    ├── engenharia-agentica-contexto-guardrails-e-criatividade.html
    ├── como-construi-sistema-suporte-cliente-ia-nivel-producao.html
    ├── fluxos-de-trabalho-agenticos-don-syme.html
    └── roteiro-engenheiro-ia-para-desenvolvedores-de-software.html
```

## Rodar localmente

```bash
cd ~/code/video-to-text
python3 -m http.server 8899 --bind 0.0.0.0
# http://localhost:8899
# Rede local (celular): http://<SEU-IP-LOCAL>:8899
```

## Adicionar novo artigo

### Pipeline — YouTube (Claude traduz)

```bash
python3 scripts/pipeline.py \
  'https://youtu.be/VIDEO_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

### Pipeline — Twitter/X (Claude traduz)

```bash
python3 scripts/pipeline.py \
  'https://x.com/user/status/TWEET_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

O pipeline detecta automaticamente o provider pela URL.
- **YouTube**: captura legendas via `youtube-transcript-api`
- **Twitter/X**: baixa áudio via `yt-dlp`, transcreve via `mlx-whisper` (local, Apple Silicon)

Aguarda a tradução via Claude/Hermes e gera o HTML.
O Claude lê `/tmp/transcript_ID.txt` e salva a tradução em `/tmp/ID_pt.txt`.

### Pipeline (local — modelo open source)

```bash
python3 scripts/pipeline.py \
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
python3 scripts/fetch_transcript.py \
  'https://youtu.be/VIDEO_ID' --text-only --timestamps \
  2>/dev/null > /tmp/transcript_VIDEO_ID.txt
```

#### 2. Traduzir

**Via Claude (default):** Pedir ao Claude para ler `/tmp/transcript_VIDEO_ID.txt` e produzir um `.txt` com:
- Português brasileiro natural
- Seções no formato abaixo
- Sem timestamps, sem [music], sem propagandas, sem filler words
- Salvar em `/tmp/VIDEO_ID_pt.txt`

**Via modelo local:** `python3 scripts/translate_local.py /tmp/transcript_VIDEO_ID.txt /tmp/VIDEO_ID_pt.txt`

O output (de ambos) é um `.txt` com seções no formato:
```
================================================================================
NOME DA SEÇÃO EM MAIÚSCULO

Parágrafo do conteúdo...
```

#### 3. Gerar HTML

```bash
python3 scripts/build_html.py \
  VIDEO_ID \
  'Título do Artigo' \
  'Subtítulo / Fonte' \
  'https://youtu.be/VIDEO_ID' \
  /tmp/VIDEO_ID_pt.txt \
  leituras/slug-do-titulo.html
```

### 4. Adicionar card no index.html

Inserir novo `<a class="card">` em `index.html` com:
- `href="leituras/slug-do-titulo.html"`
- Título, meta (fonte, autor), descrição resumida
- `<div class="progress-info" id="p-VIDEOID"></div>`
- No `<script>` do index.html, adicionar: `showProgress('reading_VIDEO_ID_', 'p-VIDEOID');`

### 5. Commit

```bash
git add leituras/slug-do-titulo.html index.html
git commit -m 'feat: adiciona artigo — Título do Vídeo'
```

## Scripts

| Script | Uso |
|--------|-----|
| `scripts/pipeline.py` | Orquestrador: URL → HTML. Detecta provider automaticamente (YouTube, Twitter/X) |
| `scripts/providers/` | Abstração multi-provider. Cada provider implementa `detect()`, `extract_id()`, `fetch_transcript()` |
| `scripts/fetch_transcript.py` | CLI standalone: captura transcrição do YouTube via `youtube-transcript-api` |
| `scripts/translate_local.py` | Traduz transcrição para PT-BR via LLM local (`mlx-vlm`). Usado com `--local` |
| `scripts/build_html.py` | Gera HTML referenciando `../css/style.css` e `../js/reader.js` |

## Arquivos compartilhados

| Arquivo | Papel |
|---------|-------|
| `css/style.css` | CSS centralizado: temas (sépia/claro/escuro), classes `.page-index` e `.page-article` |
| `js/reader.js` | JS de leitura: tema, barra de progresso, salvar posição, resume banner. Lê `data-storage-key` do `<body>` |

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
