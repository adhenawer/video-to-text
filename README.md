# video-to-text

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
scripts/providers/               — detecta provider, captura transcrição
  ├── youtube.py                 — legendas via youtube-transcript-api
  └── twitter.py                 — áudio via yt-dlp → transcrição via mlx-whisper
    ↓
Claude (tradução)                — traduz para PT-BR, remove timestamps/ads/ruídos,
                                   organiza em seções temáticas
    ↓
scripts/build_html.py            — gera o HTML com o design system do projeto
    ↓
index.html                       — card adicionado ao índice com descrição e progresso
    ↓
Artigo publicado                 — acessível localmente ou via GitHub Pages
```

---

## Arquitetura multi-provider

O sistema usa uma abstração de providers em `scripts/providers/` que permite suportar diferentes fontes de vídeo. Cada provider implementa:

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

Para adicionar um novo provider (ex: Vimeo), basta criar um novo módulo em `scripts/providers/` e registrá-lo em `__init__.py`.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Interface | [Hermes](https://github.com/NousResearch/hermes-agent) — agente via WhatsApp/CLI |
| Modelo | Claude (Anthropic) via Hermes |
| Transcrição (YouTube) | [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) |
| Transcrição (Twitter/X) | [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [mlx-whisper](https://github.com/ml-explore/mlx-examples) |
| Tradução / organização | Claude (LLM) ou Gemma 4 local (mlx-lm) |
| Build | `scripts/build_html.py` — Python puro, sem dependências externas |
| Frontend | HTML estático — zero frameworks, zero build steps |
| Hosting | GitHub Pages ou qualquer servidor estático |

---

## Setup completo

### 1. Instalar o Hermes

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
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
python3 scripts/pipeline.py \
  'https://youtu.be/VIDEO_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

### Twitter/X (Claude traduz)

```bash
python3 scripts/pipeline.py \
  'https://x.com/user/status/TWEET_ID' \
  --title 'Título do Artigo' \
  --subtitle 'Fonte / Canal' \
  --slug 'slug-do-titulo'
```

### Tradução local (Gemma 4)

```bash
python3 scripts/pipeline.py \
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
python3 scripts/fetch_transcript.py 'https://youtu.be/owmJyKVu5f8' \
  --text-only --timestamps > /tmp/transcript_owmJyKVu5f8.txt
```

Para Twitter/X, o pipeline usa `yt-dlp` para baixar o áudio e `mlx-whisper` para transcrever localmente no Apple Silicon.

**3. Claude traduz e organiza**
O agente lê a transcrição e produz um `.txt` limpo em português brasileiro, dividido em seções temáticas, sem timestamps, propagandas ou vícios de linguagem oral.

**4. O HTML é gerado**
```bash
python3 scripts/build_html.py \
  owmJyKVu5f8 \
  'Título do Artigo' \
  'Fonte / Canal' \
  'https://youtu.be/owmJyKVu5f8' \
  /tmp/owmJyKVu5f8_pt.txt \
  leituras/slug-do-titulo.html
```

**5. O card é adicionado ao índice**
O agente edita `index.html` inserindo o novo card com título, descrição e link.

**6. Commit e push**
```bash
git add leituras/slug-do-titulo.html index.html
git commit -m 'feat: adiciona artigo — Título do Vídeo'
git push
```

> Ver [CLAUDE.md](CLAUDE.md) para documentação completa do projeto.

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

1. [Chefe do Claude Code: o que acontece depois que a programação for resolvida](https://adhenawer.github.io/video-to-text/leituras/chefe-do-claude-code-o-que-acontece-depois-que-a-programacao-for-resolvida.html)
2. [Estado da IA em 2026: ponto de inflexão — Simon Willison](https://adhenawer.github.io/video-to-text/leituras/estado-da-ia-2026-ponto-de-inflexao-simon-willison.html)
3. [Práticas de engenharia para agentes de código — Simon Willison](https://adhenawer.github.io/video-to-text/leituras/praticas-de-engenharia-para-agentes-de-codigo-simon-willison.html)
4. [De IDEs para Agentes de IA — Steve Yegge](https://adhenawer.github.io/video-to-text/leituras/de-ides-para-agentes-de-ia-steve-yegge.html)
5. [Engenheiro sênior: fluxo de desenvolvimento com especificações e IA](https://adhenawer.github.io/video-to-text/leituras/engenheiro-senior-fluxo-desenvolvimento-especificacoes-ia.html)
6. [Um agente não é suficiente: programação agêntica além do Claude Code](https://adhenawer.github.io/video-to-text/leituras/um-agente-nao-e-suficiente-programacao-agentica-alem-do-claude-code.html)
7. [Do prompt à produção: o que é engenharia agêntica](https://adhenawer.github.io/video-to-text/leituras/do-prompt-a-producao-o-que-e-engenharia-agentica.html)
8. [Engenharia agêntica: contexto, guardrails e criatividade](https://adhenawer.github.io/video-to-text/leituras/engenharia-agentica-contexto-guardrails-e-criatividade.html)
9. [Como construí um sistema de suporte ao cliente com IA de nível produção](https://adhenawer.github.io/video-to-text/leituras/como-construi-sistema-suporte-cliente-ia-nivel-producao.html)
10. [Fluxos de trabalho agênticos — Don Syme](https://adhenawer.github.io/video-to-text/leituras/fluxos-de-trabalho-agenticos-don-syme.html)
11. [Roteiro: engenheiro de IA para desenvolvedores de software](https://adhenawer.github.io/video-to-text/leituras/roteiro-engenheiro-ia-para-desenvolvedores-de-software.html)
12. [Política corporativa em tech — Ethan Evans (ex-VP Amazon)](https://adhenawer.github.io/video-to-text/leituras/politica-corporativa-tech-tudo-que-ninguem-te-conta.html)
13. [Por que paramos de construir agentes e começamos a construir skills — Anthropic](https://adhenawer.github.io/video-to-text/leituras/por-que-paramos-de-construir-agentes-e-comecamos-a-construir-skills.html) *(via Twitter/X)*
