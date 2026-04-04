#!/usr/bin/env python3
"""
Build HTML blog posts from YouTube transcripts.
Reads translated .txt files and generates HTML with the standard template.
CSS and JS are loaded from ../css/style.css and ../js/reader.js.
"""
import re, os, sys


def make_html(vid_id, title, subtitle, url, txt_path):
    """Read translated txt, parse sections, return full HTML string."""
    with open(txt_path, 'r') as f:
        raw = f.read()

    # Strip line numbers if present
    text = re.sub(r'^\s*\d+\|', '', raw, flags=re.MULTILINE)
    lines = text.strip().split('\n')

    html_parts = []
    toc_parts = []
    section_id = 0
    prev_was_sep = False

    # Skip title block (everything before first ====)
    start = 0
    for start, line in enumerate(lines):
        if line.strip().startswith('=' * 10):
            break

    prev_was_sep = True
    for line in lines[start+1:]:
        stripped = line.strip()
        if stripped.startswith('=' * 10):
            prev_was_sep = True
            continue
        if not stripped and prev_was_sep:
            continue
        if prev_was_sep and stripped:
            prev_was_sep = False
            is_short = len(stripped) < 100
            is_paragraph_start = any(stripped.startswith(p) for p in [
                'Lenny ', 'Boris ', 'Simon ', 'Steve ', 'Don ', 'Para ', 'Ele ',
                'Ela ', 'Essa ', 'Uma ', 'O ', 'A ', 'Na ', 'No ', 'Em ', 'Como ',
                'Isso ', 'Ao ', 'Os ', 'As ', 'Se ', 'Com ', 'Por ', 'Quando ',
                'Durante ', 'Após ', 'Antes ', 'Nessa ', 'Nesse '
            ])
            if is_short and not is_paragraph_start:
                section_id += 1
                slug = f"s{section_id}"
                toc_parts.append(f'<li><a href="#{slug}">{stripped}</a></li>')
                html_parts.append(f'<h2 id="{slug}">{stripped}</h2>')
                continue
            else:
                formatted = re.sub(r'"([^"]+)"', r'&ldquo;\1&rdquo;', stripped)
                html_parts.append(f'<p>{formatted}</p>')
                continue
        prev_was_sep = False
        if not stripped:
            continue
        formatted = re.sub(r'"([^"]+)"', r'&ldquo;\1&rdquo;', stripped)
        html_parts.append(f'<p>{formatted}</p>')

    toc_html = '\n'.join(toc_parts)
    body_html = '\n'.join(html_parts)
    storage_key = f'reading_{vid_id}_'

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="../css/style.css">
</head>
<body class="page-article" data-storage-key="{storage_key}">
<div class="progress" id="progress"></div>
<div class="reading-pct" id="readingPct"></div>
<div class="container">
  <a href="../index.html" class="back-home">← Voltar ao índice</a>
  <header>
    <h1>{title}</h1>
    <p class="meta">{subtitle}</p>
    <p class="meta"><a href="{url}" target="_blank">🎥 Assistir no YouTube</a></p>
  </header>
  <div class="theme-bar">
    <button class="theme-btn active" onclick="setTheme('light')">☀️ Sépia</button>
    <button class="theme-btn" onclick="setTheme('cool')">🌤️ Claro</button>
    <button class="theme-btn" onclick="setTheme('dark')">🌙 Escuro</button>
  </div>
  <nav>
    <h3>📑 Índice</h3>
    <ol>
{toc_html}
    </ol>
  </nav>
{body_html}
</div>
<a href="#" class="back-top" id="backTop">↑</a>
<div class="resume-banner" id="resumeBanner">
  <span id="resumeText">📖 Continuar de onde parou</span>
  <div>
    <button onclick="resumeReading()">Continuar</button>
    <button class="dismiss" onclick="dismissResume()">✕</button>
  </div>
</div>
<script src="../js/reader.js"></script>
</body>
</html>'''


if __name__ == '__main__':
    vid_id  = sys.argv[1]
    title   = sys.argv[2]
    subtitle= sys.argv[3]
    url     = sys.argv[4]
    txt_in  = sys.argv[5]
    html_out= sys.argv[6]
    html = make_html(vid_id, title, subtitle, url, txt_in)
    with open(html_out, 'w') as f:
        f.write(html)
    print(f"OK {html_out} ({len(html):,} bytes)")
