# video-to-text

Transforma vídeos e podcasts do YouTube em artigos de leitura — traduzidos para português brasileiro, organizados por seções e publicados como HTML estático.

## Como funciona

O fluxo é inteiramente conversacional via **[Hermes](https://github.com/hermesapp/hermes) + Claude**. Basta mandar a URL de um vídeo do YouTube no chat:

```
https://youtu.be/VIDEO_ID
```

O agente cuida de tudo automaticamente:

```
URL do YouTube
    ↓
fetch_transcript.py       — captura a transcrição via youtube-transcript-api
    ↓
Claude (tradução)         — traduz para PT-BR, remove timestamps/ads/ruídos,
                            organiza em seções temáticas
    ↓
build_html.py             — gera o HTML com o design system do projeto
    ↓
index.html                — card adicionado automaticamente ao índice
    ↓
Artigo publicado          — acessível localmente ou via GitHub Pages
```

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Interface | [Hermes](https://github.com/hermesapp/hermes) — agente de IA via WhatsApp/CLI |
| Modelo | Claude (Anthropic) |
| Transcrição | [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) |
| Tradução/organização | Claude (processamento de linguagem natural) |
| Build | `scripts/build_html.py` — Python puro, sem dependências externas |
| Frontend | HTML estático — zero frameworks, zero build steps |
| Hosting | GitHub Pages ou qualquer servidor estático |

## Leitura

- 3 temas: ☀️ Sépia (padrão, estilo Kindle) · 🌤️ Claro · 🌙 Escuro
- Progresso de leitura salvo por dispositivo — retoma de onde parou
- Índice com % lido por artigo
- Responsivo para mobile

## Rodar localmente

```bash
git clone https://github.com/<SEU-USUARIO>/video-to-text
cd video-to-text
python3 -m http.server 8080
# Acesse: http://localhost:8080
```

## Adicionar um artigo

Ver [CLAUDE.md](CLAUDE.md) para o passo a passo completo.

Resumo:

```bash
# 1. Capturar transcrição
python3 scripts/fetch_transcript.py 'https://youtu.be/ID' \
  --text-only --timestamps > /tmp/raw.txt

# 2. Traduzir (via Claude)

# 3. Gerar HTML
python3 scripts/build_html.py ID 'Título' 'Fonte' 'URL' \
  /tmp/traduzido.txt leituras/slug.html
```

## Artigos

1. [Chefe do Claude Code: o que acontece depois que a programação for resolvida](leituras/chefe-do-claude-code-o-que-acontece-depois-que-a-programacao-for-resolvida.html)
2. [Estado da IA em 2026: ponto de inflexão — Simon Willison](leituras/estado-da-ia-2026-ponto-de-inflexao-simon-willison.html)
3. [Práticas de engenharia para agentes de código — Simon Willison](leituras/praticas-de-engenharia-para-agentes-de-codigo-simon-willison.html)
4. [De IDEs para Agentes de IA — Steve Yegge](leituras/de-ides-para-agentes-de-ia-steve-yegge.html)
5. [Engenheiro sênior: fluxo de desenvolvimento com especificações e IA](leituras/engenheiro-senior-fluxo-desenvolvimento-especificacoes-ia.html)
6. [Um agente não é suficiente: programação agêntica além do Claude Code](leituras/um-agente-nao-e-suficiente-programacao-agentica-alem-do-claude-code.html)
7. [Do prompt à produção: o que é engenharia agêntica](leituras/do-prompt-a-producao-o-que-e-engenharia-agentica.html)
8. [Engenharia agêntica: contexto, guardrails e criatividade](leituras/engenharia-agentica-contexto-guardrails-e-criatividade.html)
9. [Como construí um sistema de suporte ao cliente com IA de nível produção](leituras/como-construi-sistema-suporte-cliente-ia-nivel-producao.html)
10. [Fluxos de trabalho agênticos — Don Syme](leituras/fluxos-de-trabalho-agenticos-don-syme.html)
11. [Roteiro: engenheiro de IA para desenvolvedores de software](leituras/roteiro-engenheiro-ia-para-desenvolvedores-de-software.html)
