#!/usr/bin/env python3
"""
Build HTML blog posts from translated transcripts.
Reads translated .txt files and generates HTML with the standard template.
Optionally embeds presentation slides from a slides JSON manifest.
CSS and JS are loaded from ../css/style.css and ../js/reader.js.
"""
import json, re, os, sys


def _load_slides(slides_json_path):
    """Load slides JSON manifest. Returns list of slide dicts or empty list."""
    if not slides_json_path or not os.path.exists(slides_json_path):
        return []
    with open(slides_json_path, 'r') as f:
        return json.load(f)


def _match_slides_to_sections(slides, section_count):
    """
    Distribute slides across sections proportionally by timestamp.
    Returns dict: {section_index: [slide, ...]}.
    """
    if not slides or section_count == 0:
        return {}

    total_duration = slides[-1]["timestamp"] if slides else 1
    if total_duration == 0:
        total_duration = 1

    mapping = {}
    for slide in slides:
        proportion = slide["timestamp"] / total_duration
        section_idx = min(int(proportion * section_count), section_count - 1)
        mapping.setdefault(section_idx, []).append(slide)

    return mapping


def _slide_html(slide):
    """Generate HTML for a single slide figure."""
    ts = slide.get("timestamp_fmt", "")
    path = slide["path"]
    return (
        f'<figure class="slide-figure">'
        f'<img class="slide-img" src="../{path}" alt="Slide — {ts}" loading="lazy">'
        f'<figcaption class="slide-caption">Slide — {ts}</figcaption>'
        f'</figure>'
    )


def make_html(vid_id, title, subtitle, url, txt_path,
              link_text="🎥 Assistir no YouTube", slides_json_path=None,
              lang="pt_br", slug=None, pt_slug=None, en_slug=None):
    """Read translated txt, parse sections, return full HTML string."""
    with open(txt_path, 'r') as f:
        raw = f.read()

    slides = _load_slides(slides_json_path)

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
                section_slug = f"s{section_id}"
                toc_parts.append(f'<li><a href="#{section_slug}">{stripped}</a></li>')
                html_parts.append(f'<h2 id="{section_slug}">{stripped}</h2>')
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

    # Inject slides into HTML at section boundaries
    if slides and section_id > 0:
        slide_map = _match_slides_to_sections(slides, section_id)
        # Walk through html_parts and inject slides after each <h2>
        new_parts = []
        current_section = 0
        for part in html_parts:
            new_parts.append(part)
            if part.startswith('<h2 '):
                current_section += 1
                section_slides = slide_map.get(current_section - 1, [])
                for slide in section_slides:
                    new_parts.append(_slide_html(slide))
        html_parts = new_parts

    toc_html = '\n'.join(toc_parts)
    body_html = '\n'.join(html_parts)
    storage_key = f'reading_{vid_id}_'

    # Extract first paragraph as description for SEO/LLMO
    first_para = ""
    for part in html_parts:
        if part.startswith('<p>'):
            first_para = re.sub(r'<[^>]+>', '', part)
            first_para = first_para[:200].rsplit(' ', 1)[0] + "..." if len(first_para) > 200 else first_para
            break

    # Collect section titles for JSON-LD
    section_titles = [re.sub(r'<[^>]+>', '', t) for t in toc_parts]

    # Escape quotes for JSON
    desc_json = first_para.replace('"', '\\"')
    title_json = title.replace('"', '\\"')
    subtitle_json = subtitle.replace('"', '\\"')

    # JSON-LD structured data (Article schema)
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": first_para,
        "author": {"@type": "Person", "name": subtitle.split("·")[0].strip() if "·" in subtitle else subtitle},
        "publisher": {"@type": "Organization", "name": "Leituras — Podcasts & Vídeos Traduzidos"},
        "inLanguage": "pt-BR" if lang == "pt_br" else "en",
        "isAccessibleForFree": True,
        "url": url,
        "articleSection": section_titles,
    }, ensure_ascii=False)

    # Wrap body content in semantic <article> with <section> tags
    semantic_parts = []
    in_section = False
    for part in html_parts:
        if part.startswith('<h2 '):
            if in_section:
                semantic_parts.append('</section>')
            semantic_parts.append('<section>')
            in_section = True
        semantic_parts.append(part)
    if in_section:
        semantic_parts.append('</section>')

    body_html = '\n'.join(semantic_parts)

    # Language configuration
    is_ptbr = lang == "pt_br"
    html_lang = "pt-BR" if is_ptbr else "en"
    og_locale = "pt_BR" if is_ptbr else "en_US"
    back_label = "← Voltar ao índice" if is_ptbr else "← Back to index"
    toc_label = "📑 Índice" if is_ptbr else "📑 Table of Contents"
    toc_aria = "Índice do artigo" if is_ptbr else "Article table of contents"
    resume_text = "📖 Continuar de onde parou" if is_ptbr else "📖 Resume where you left off"
    resume_btn = "Continuar" if is_ptbr else "Resume"
    site_brand = "Leituras" if is_ptbr else "Readings"

    # Determine pt_slug and en_slug for hreflang alternates
    # Backwards compat: if only `slug` is passed, derive the other side from it
    cur_slug = slug or vid_id
    if pt_slug is None:
        pt_slug = cur_slug if is_ptbr else cur_slug
    if en_slug is None:
        en_slug = cur_slug if not is_ptbr else cur_slug

    pt_href = f"../pt_br/{pt_slug}.html"
    en_href = f"../original/{en_slug}.html"

    return f'''<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{first_para}">
<meta name="author" content="{subtitle}">
<link rel="alternate" hreflang="pt-BR" href="{pt_href}">
<link rel="alternate" hreflang="en" href="{en_href}">
<link rel="alternate" hreflang="x-default" href="{pt_href}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{first_para}">
<meta property="og:locale" content="{og_locale}">
<meta property="og:site_name" content="Leituras — Podcasts &amp; Vídeos Traduzidos">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{first_para}">
<script type="application/ld+json">
{jsonld}
</script>
<link rel="stylesheet" href="../../css/style.css">
</head>
<body class="page-article" data-storage-key="{storage_key}">
<header class="site-header">
  <a class="site-brand" href="../../index.html">🎙 {site_brand}</a>
  <div class="lang-bar">
    <button class="lang-btn" data-lang="pt-BR" aria-label="Português">🇧🇷 PT</button>
    <button class="lang-btn" data-lang="en" aria-label="English">🇺🇸 EN</button>
  </div>
</header>
<div class="progress" id="progress"></div>
<div class="reading-pct" id="readingPct"></div>
<article class="container">
  <a href="../../index.html" class="back-home">{back_label}</a>
  <header>
    <h1>{title}</h1>
    <p class="meta"><cite>{subtitle}</cite></p>
    <p class="meta"><a href="{url}" target="_blank" rel="noopener">{link_text}</a></p>
  </header>
  <div class="theme-bar">
    <button class="theme-btn active" onclick="setTheme('light')">☀️ Sépia</button>
    <button class="theme-btn" onclick="setTheme('cool')">🌤️ Claro</button>
    <button class="theme-btn" onclick="setTheme('dark')">🌙 Escuro</button>
  </div>
  <nav aria-label="{toc_aria}">
    <h3>{toc_label}</h3>
    <ol>
{toc_html}
    </ol>
  </nav>
{body_html}
</article>
<a href="#" class="back-top" id="backTop">↑</a>
<div class="resume-banner" id="resumeBanner">
  <span id="resumeText">{resume_text}</span>
  <div>
    <button onclick="resumeReading()">{resume_btn}</button>
    <button class="dismiss" onclick="dismissResume()">✕</button>
  </div>
</div>
<script src="../../js/reader.js"></script>
<script src="../../js/lang.js"></script>
</body>
</html>'''


if __name__ == '__main__':
    vid_id   = sys.argv[1]
    title    = sys.argv[2]
    subtitle = sys.argv[3]
    url      = sys.argv[4]
    txt_in   = sys.argv[5]
    html_out = sys.argv[6]
    link_text  = sys.argv[7] if len(sys.argv) > 7 else "🎥 Assistir no YouTube"
    slides_json = sys.argv[8] if len(sys.argv) > 8 else None
    html = make_html(vid_id, title, subtitle, url, txt_in, link_text, slides_json)
    with open(html_out, 'w') as f:
        f.write(html)
    print(f"OK {html_out} ({len(html):,} bytes)")
