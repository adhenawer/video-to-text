# CLAUDE.md — Projeto video-to-text

Site estático com artigos de podcasts e vídeos sobre IA traduzidos para português brasileiro. Zero dependências — HTML puro.

## Estrutura

```
video-to-text/
├── CLAUDE.md
├── README.md
├── .gitignore
├── index.html                  ← índice com todos os artigos
└── leituras/                   ← artigos individuais
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

### 1. Capturar transcrição

```bash
python3 scripts/fetch_transcript.py \
  'https://youtu.be/VIDEO_ID' --text-only --timestamps \
  2>/dev/null > /tmp/transcript_VIDEO_ID.txt
```

### 2. Traduzir e organizar

Pedir ao Claude para ler `/tmp/transcript_VIDEO_ID.txt` e produzir um `.txt` com:
- Português brasileiro natural
- Seções no formato:

```
================================================================================
NOME DA SEÇÃO EM MAIÚSCULO

Parágrafo do conteúdo...
```

- Sem timestamps, sem [music], sem propagandas, sem filler words
- Salvar em `/tmp/VIDEO_ID_pt.txt`

### 3. Gerar HTML com build_html.py

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

Ambos os scripts estão em `scripts/` e são parte do repositório.

| Script | Uso |
|--------|-----|
| `scripts/fetch_transcript.py` | Captura transcrição de qualquer URL do YouTube via `youtube-transcript-api` |
| `scripts/build_html.py` | Converte `.txt` traduzido em HTML com o design system do projeto |

Instalar dependência do fetch:
```bash
pip install youtube-transcript-api
```

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
