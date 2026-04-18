#!/usr/bin/env python3
"""
Backfill timestamps + regenerate HTMLs for a single post.

Usage:
    python3 scripts/backfill_one.py <video_id> \
        --en-title "..." --en-subtitle "..." \
        [--pt-ts "0:00,1:23,..."] [--en-ts "0:00,..."]

If --pt-ts / --en-ts are omitted, auto-inference is used.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJ, 'src'))
sys.path.insert(0, os.path.join(PROJ, 'scripts'))

from build_html import make_html
from infer_section_timestamps import infer
from extract_ptbr_from_html import (
    SECTION_RE, PARA_RE, _clean, _strip_existing_ts,
)


def _ptbr_section_count(html_path):
    with open(html_path) as f:
        return len(SECTION_RE.findall(f.read()))


def _en_section_count(en_txt_path):
    with open(en_txt_path) as f:
        content = f.read()
    return content.count('=' * 10) // 2 if content.count('=' * 10) > 0 else len(re.findall(r'^=+$', content, re.M))


def _section_count_in_txt(txt_path):
    """Count section headings (lines right after a separator)."""
    with open(txt_path) as f:
        lines = f.read().split('\n')
    count = 0
    expect = False
    for line in lines:
        s = line.strip()
        if s.startswith('=' * 10):
            expect = True
            continue
        if expect and s:
            count += 1
            expect = False
    return count


def _propose_pt_timestamps_from_en(en_ts_list, n_pt_sections):
    """When PT has fewer sections than EN, distribute EN timestamps coarsely."""
    if not en_ts_list:
        return []
    if n_pt_sections >= len(en_ts_list):
        return en_ts_list[:n_pt_sections]
    # Pick every (len(en) / n_pt)th timestamp
    step = len(en_ts_list) / n_pt_sections
    return [en_ts_list[min(int(i * step), len(en_ts_list) - 1)] for i in range(n_pt_sections)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('vid')
    ap.add_argument('--en-title', required=True)
    ap.add_argument('--en-subtitle', required=True)
    ap.add_argument('--pt-ts', default=None, help='comma-separated PT timestamps (override auto)')
    ap.add_argument('--en-ts', default=None, help='comma-separated EN timestamps (override auto)')
    args = ap.parse_args()

    with open(os.path.join(PROJ, 'transcripts', 'index.json')) as f:
        idx = json.load(f)

    entry = next((e for e in idx if e['video_id'] == args.vid), None)
    if entry is None:
        sys.exit(f'video_id not found: {args.vid}')

    provider = entry['provider']
    pt_slug = entry['slug']
    en_slug = entry.get('slug_en')
    raw_path = os.path.join(PROJ, 'transcripts', provider, f'{args.vid}.txt')
    pt_txt = os.path.join(PROJ, 'transcripts', provider, f'{args.vid}_pt.txt')
    en_txt = os.path.join(PROJ, 'transcripts', provider, f'{args.vid}_en.txt')
    pt_html = os.path.join(PROJ, 'docs', 'posts', 'pt_br', f'{pt_slug}.html')
    en_html = os.path.join(PROJ, 'docs', 'posts', 'original', f'{en_slug}.html') if en_slug else None

    # Step 1: build/update _en.txt timestamps
    if not os.path.exists(en_txt):
        sys.exit(f'EN txt missing: {en_txt}')
    if args.en_ts:
        en_ts_list = args.en_ts.split(',')
    else:
        en_ts_list, en_sections = infer(raw_path, en_txt)
        for ts, (title, _) in zip(en_ts_list, en_sections):
            print(f'  EN [{ts}] {title}', file=sys.stderr)
    subprocess.run(['python3', os.path.join(PROJ, 'scripts', 'inject_section_timestamps.py'),
                    en_txt, ','.join(en_ts_list)], check=True)

    # Step 2: build/update _pt.txt timestamps
    pt_ts_list = None
    if args.pt_ts:
        pt_ts_list = args.pt_ts.split(',')

    if os.path.exists(pt_txt):
        n_pt = _section_count_in_txt(pt_txt)
        if pt_ts_list is None:
            pt_ts_list = _propose_pt_timestamps_from_en(en_ts_list, n_pt)
        subprocess.run(['python3', os.path.join(PROJ, 'scripts', 'inject_section_timestamps.py'),
                        pt_txt, ','.join(pt_ts_list)], check=True)
    elif os.path.exists(pt_html):
        # Extract from HTML with timestamps
        n_pt = _ptbr_section_count(pt_html)
        if pt_ts_list is None:
            pt_ts_list = _propose_pt_timestamps_from_en(en_ts_list, n_pt)
        ts_arg = ','.join(f'{i+1}:{t}' for i, t in enumerate(pt_ts_list))
        subprocess.run(['python3', os.path.join(PROJ, 'scripts', 'extract_ptbr_from_html.py'),
                        pt_html, pt_txt, '--timestamps', ts_arg], check=True)
    else:
        print(f'WARN: no PT source for {pt_slug}', file=sys.stderr)

    # Step 3: regenerate PT HTML
    link_text_pt = '🐦 Ver no Twitter/X' if provider == 'twitter' else '🎥 Assistir no YouTube'
    if os.path.exists(pt_txt):
        html_out = make_html(
            vid_id=args.vid, title=entry['title'], subtitle=entry['subtitle'],
            url=entry['url'], txt_path=pt_txt, link_text=link_text_pt,
            lang='pt_br', slug=pt_slug, pt_slug=pt_slug, en_slug=en_slug,
            provider=provider,
        )
        with open(pt_html, 'w') as f:
            f.write(html_out)
        print(f'  PT HTML: {pt_html}')

    # Step 4: regenerate EN HTML
    if en_slug and en_html:
        link_text_en = '🐦 View on Twitter/X' if provider == 'twitter' else '🎥 Watch on YouTube'
        html_out = make_html(
            vid_id=args.vid, title=args.en_title, subtitle=args.en_subtitle,
            url=entry['url'], txt_path=en_txt, link_text=link_text_en,
            lang='original', slug=en_slug, pt_slug=pt_slug, en_slug=en_slug,
            provider=provider,
        )
        with open(en_html, 'w') as f:
            f.write(html_out)
        print(f'  EN HTML: {en_html}')

    # Step 5: remove flag
    if entry.get('timestamps_backfilled') is False:
        del entry['timestamps_backfilled']
        with open(os.path.join(PROJ, 'transcripts', 'index.json'), 'w') as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
        print('  Flag removed from index.json')

    print(f'\nDONE {args.vid} ({pt_slug})')


if __name__ == '__main__':
    main()
