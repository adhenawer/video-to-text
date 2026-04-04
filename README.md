# video-to-text

Transforma vídeos e podcasts do YouTube em artigos de leitura — traduzidos para português brasileiro, organizados por seções e publicados como HTML estático.

## Por que este projeto existe

Eu prefiro ler. Quando quero aprender algo, um artigo de 10 minutos me entrega mais do que um vídeo de 1h. Leio no meu ritmo, pulo o que não interessa, volto no que precisa de mais atenção.

Estou estudando IA e o volume de conteúdo relevante em podcasts e vídeos é enorme. Não tenho tempo de assistir tudo, mas não quero perder nada. A solução foi automatizar: mando o link de um vídeo pelo WhatsApp para o [Hermes](https://github.com/NousResearch/hermes-agent) e ele devolve o artigo pronto, traduzido e organizado em seções.

A ideia é consumir o conteúdo pelo celular, então o formato importa. Cada artigo é um post limpo, dividido em seções com índice clicável, progresso salvo e retomada automática. As cores seguem a paleta sépia de e-readers como o Kindle — conforto para leitura longa, sem cansar a vista.

No fim, este projeto resolve um problema pessoal: consumir mais conteúdo em menos tempo, no formato que funciona melhor pra mim.

---

## Como funciona

O fluxo é inteiramente conversacional via **[Hermes](https://github.com/NousResearch/hermes-agent) + Claude**. Basta mandar a URL de um vídeo do YouTube no chat (WhatsApp, Telegram ou terminal):

```
https://youtu.be/VIDEO_ID
```

O agente cuida de tudo automaticamente:

```
URL do YouTube
    ↓
scripts/fetch_transcript.py   — captura a transcrição via youtube-transcript-api
    ↓
Claude (tradução)             — traduz para PT-BR, remove timestamps/ads/ruídos,
                                organiza em seções temáticas
    ↓
scripts/build_html.py         — gera o HTML com o design system do projeto
    ↓
index.html                    — card adicionado ao índice com descrição e progresso
    ↓
Artigo publicado              — acessível localmente ou via GitHub Pages
```

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Interface | [Hermes](https://github.com/NousResearch/hermes-agent) — agente via WhatsApp/CLI |
| Modelo | Claude (Anthropic) via Hermes |
| Transcrição | [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) |
| Tradução / organização | Claude (LLM) |
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
pip install youtube-transcript-api
```

### 5. Rodar o servidor local

```bash
python3 -m http.server 8080
# http://localhost:8080
# Rede local (celular): http://<SEU-IP-LOCAL>:8080
```

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
