#!/usr/bin/env python3
"""
Build HTML blog posts from YouTube transcripts.
Reads translated .txt files and generates HTML with the standard template.
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
<style>
  :root {{
    --bg:#FAF4E8;--surface:#F0E6D0;--border:#D4B896;--text:#3D3529;
    --text-heading:#2C2416;--text-muted:#7A6F5F;--accent:#C17C3E;
    --link:#8B5E3C;--progress-start:#C17C3E;--progress-end:#8B5E3C;
    --back-top-bg:#C17C3E;--back-top-text:#FAF4E8;--toc-bg:#F0E9D8;
    --toc-border:#D4B896;--theme-btn-bg:#EDE4D3;--resume-bg:#C17C3E;--resume-text:#FAF4E8;
  }}
  [data-theme="dark"]{{
    --bg:#1E1E24;--surface:#252530;--border:#4A4A56;--text:#D4D0C8;
    --text-heading:#E8E4DC;--text-muted:#8A8A94;--accent:#C4956A;
    --link:#9BB8D4;--progress-start:#C4956A;--progress-end:#9BB8D4;
    --back-top-bg:#C4956A;--back-top-text:#1E1E24;--toc-bg:#282830;
    --toc-border:#4A4A56;--theme-btn-bg:#33333C;--resume-bg:#C4956A;--resume-text:#1E1E24;
  }}
  [data-theme="cool"]{{
    --bg:#F0F2F5;--surface:#E8EBF0;--border:#B8C0CC;--text:#2D3748;
    --text-heading:#1A2332;--text-muted:#718096;--accent:#E07850;
    --link:#4A7C9B;--progress-start:#E07850;--progress-end:#4A7C9B;
    --back-top-bg:#4A7C9B;--back-top-text:#F0F2F5;--toc-bg:#E4E7EC;
    --toc-border:#B8C0CC;--theme-btn-bg:#D8DBE2;--resume-bg:#4A7C9B;--resume-text:#F0F2F5;
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  html{{scroll-behavior:smooth}}
  body{{font-family:Georgia,'Times New Roman',serif;background:var(--bg);color:var(--text);line-height:1.7;-webkit-font-smoothing:antialiased;transition:background .3s,color .3s}}
  .container{{max-width:680px;margin:0 auto;padding:20px 24px 100px}}
  header{{text-align:center;padding:48px 0 32px;border-bottom:1px solid var(--border);margin-bottom:32px}}
  header h1{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.65em;font-weight:700;line-height:1.3;color:var(--text-heading);margin-bottom:14px}}
  .meta{{color:var(--text-muted);font-size:.9em;margin-bottom:6px;font-family:-apple-system,sans-serif}}
  .meta a{{color:var(--link);text-decoration:none}}
  .theme-bar{{display:flex;justify-content:center;gap:8px;margin:20px 0 32px}}
  .theme-btn{{font-family:-apple-system,sans-serif;font-size:.82em;padding:8px 16px;border:1px solid var(--border);border-radius:20px;background:var(--theme-btn-bg);color:var(--text);cursor:pointer;transition:all .2s}}
  .theme-btn.active{{background:var(--accent);color:var(--bg);border-color:var(--accent)}}
  nav{{background:var(--toc-bg);border:1px solid var(--toc-border);border-radius:12px;padding:24px 28px;margin-bottom:40px}}
  nav h3{{font-family:-apple-system,sans-serif;font-size:1em;margin-bottom:12px;color:var(--accent)}}
  nav ol{{padding-left:20px}}
  nav li{{margin:6px 0;font-size:.88em;font-family:-apple-system,sans-serif}}
  nav a{{color:var(--text-muted);text-decoration:none;transition:color .2s}}
  nav a:hover{{color:var(--link)}}
  h2{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.25em;font-weight:600;color:var(--accent);margin:48px 0 18px;padding-bottom:8px;border-bottom:1px solid var(--border);scroll-margin-top:20px}}
  p{{margin-bottom:20px;font-size:1.08em;letter-spacing:.01em}}
  .progress{{position:fixed;top:0;left:0;height:3px;background:linear-gradient(90deg,var(--progress-start),var(--progress-end));z-index:999;transition:width .15s}}
  .back-top{{position:fixed;bottom:24px;right:24px;background:var(--back-top-bg);color:var(--back-top-text);width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.3em;text-decoration:none;box-shadow:0 3px 10px rgba(0,0,0,.15);opacity:0;transition:opacity .3s}}
  .back-top.show{{opacity:1}}
  .resume-banner{{position:fixed;bottom:0;left:0;right:0;background:var(--resume-bg);color:var(--resume-text);padding:14px 20px;display:flex;align-items:center;justify-content:space-between;font-family:-apple-system,sans-serif;font-size:.9em;z-index:1000;box-shadow:0 -2px 10px rgba(0,0,0,.15);transform:translateY(100%);transition:transform .3s ease}}
  .resume-banner.show{{transform:translateY(0)}}
  .resume-banner button{{background:rgba(255,255,255,.25);border:none;color:inherit;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:.9em;font-weight:600}}
  .resume-banner .dismiss{{background:none;padding:8px;font-size:1.1em;opacity:.7}}
  .reading-pct{{position:fixed;top:8px;right:12px;font-family:-apple-system,sans-serif;font-size:.75em;color:var(--text-muted);opacity:0;transition:opacity .3s;z-index:998}}
  .reading-pct.show{{opacity:1}}
  @media(max-width:600px){{
    .container{{padding:16px 20px 100px}}
    header{{padding:36px 0 24px}}
    header h1{{font-size:1.35em}}
    h2{{font-size:1.12em;margin:36px 0 14px}}
    p{{font-size:1.02em}}
    .theme-bar{{gap:6px}}
    .theme-btn{{padding:6px 12px;font-size:.78em}}
  }}
</style>
</head>
<body>
<div class="progress" id="progress"></div>
<div class="reading-pct" id="readingPct"></div>
<div class="container">
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
<script>
function getDeviceId(){{let id=localStorage.getItem('_deviceId');if(!id){{id='dev_'+Math.random().toString(36).substr(2,9)+'_'+Date.now();localStorage.setItem('_deviceId',id);}}return id;}}
const STORAGE_KEY='{storage_key}'+getDeviceId();
let saveTimer=null,resumeTarget=null;
function savePosition(){{const h=document.documentElement;const sp=h.scrollTop/(h.scrollHeight-h.clientHeight);let cs='';document.querySelectorAll('h2').forEach(el=>{{if(el.getBoundingClientRect().top<100)cs=el.id;}});localStorage.setItem(STORAGE_KEY,JSON.stringify({{scrollY:window.scrollY,scrollPct:Math.round(sp*100),section:cs,sectionTitle:cs?document.getElementById(cs)?.textContent:'',theme:document.documentElement.getAttribute('data-theme')||'light',timestamp:Date.now()}}));}}
function debounceSave(){{clearTimeout(saveTimer);saveTimer=setTimeout(savePosition,300);}}
function loadPosition(){{try{{return JSON.parse(localStorage.getItem(STORAGE_KEY));}}catch{{return null;}}}}
function resumeReading(){{if(resumeTarget)window.scrollTo({{top:resumeTarget.scrollY,behavior:'smooth'}});document.getElementById('resumeBanner').classList.remove('show');}}
function dismissResume(){{document.getElementById('resumeBanner').classList.remove('show');}}
function setTheme(theme){{if(theme==='light')document.documentElement.removeAttribute('data-theme');else document.documentElement.setAttribute('data-theme',theme);document.querySelectorAll('.theme-btn').forEach((btn,i)=>{{btn.classList.toggle('active',['light','cool','dark'][i]===theme);}});localStorage.setItem('_reading_theme',theme);savePosition();}}
const progressEl=document.getElementById('progress'),backTopEl=document.getElementById('backTop'),readingPctEl=document.getElementById('readingPct');
window.addEventListener('scroll',()=>{{const h=document.documentElement;const pct=Math.round((h.scrollTop/(h.scrollHeight-h.clientHeight))*100);progressEl.style.width=pct+'%';backTopEl.classList.toggle('show',h.scrollTop>400);readingPctEl.textContent=pct+'%';readingPctEl.classList.toggle('show',h.scrollTop>200);debounceSave();}},{{passive:true}});
(function init(){{const savedTheme=localStorage.getItem('_reading_theme')||'light';setTheme(savedTheme);const saved=loadPosition();if(saved&&saved.scrollY>300){{resumeTarget=saved;document.getElementById('resumeText').textContent='📖 Continuar: '+(saved.sectionTitle||'seção anterior')+' ('+(saved.scrollPct||0)+'%)';setTimeout(()=>document.getElementById('resumeBanner').classList.add('show'),500);setTimeout(()=>document.getElementById('resumeBanner').classList.remove('show'),8500);}}window.addEventListener('beforeunload',savePosition);document.addEventListener('visibilitychange',()=>{{if(document.hidden)savePosition();}});}})();
</script>
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
