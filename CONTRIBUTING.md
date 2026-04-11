# Contribuindo

Contribuições são bem-vindas! Aqui estão algumas formas de ajudar:

## Sugerir vídeos para tradução

Abra uma [issue](https://github.com/adhenawer/video-to-text/issues/new?template=novo-video.md) com a URL do vídeo. Aceitamos YouTube e Twitter/X em qualquer idioma.

## Adicionar novo provider

O projeto usa uma arquitetura de providers em `scripts/providers/`. Para adicionar suporte a uma nova plataforma (Vimeo, Instagram, etc.):

1. Crie `scripts/providers/novo_provider.py` implementando `detect()`, `extract_id()`, `fetch_transcript()`
2. Registre em `scripts/providers/__init__.py`
3. Teste com `python3 scripts/pipeline.py 'URL' --title 'Test' --subtitle 'Test' --slug 'test'`

## Melhorar traduções

Se encontrar erros de tradução nos artigos, abra um PR corrigindo diretamente o HTML em `leituras/`.

## Desenvolvimento local

```bash
git clone https://github.com/adhenawer/video-to-text
cd video-to-text
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m http.server 8899
```

## Convenções

- Commits: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`
- Slugs: kebab-case PT-BR sem acentos
- HTML: ver `CLAUDE.md` para design system e SEO
