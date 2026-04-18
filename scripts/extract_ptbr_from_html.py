#!/usr/bin/env python3
"""
Extract PT-BR transcript from rendered HTML back into the formatted .txt
shape used by build_html.py, optionally injecting timestamps.

Usage:
    python3 scripts/extract_ptbr_from_html.py \
        docs/posts/pt_br/<slug>.html \
        transcripts/<provider>/<vid>_pt.txt \
        [--timestamps "1:0:00,2:0:46,..."]

The --timestamps flag is a comma-separated list of `<section_index>:<mm:ss>`
pairs (1-indexed). Sections without a mapped timestamp keep no `[mm:ss]`
prefix.
"""
import argparse
import html
import re
import sys


SECTION_RE = re.compile(r'<section>\s*<h2[^>]*>(.+?)</h2>(.+?)</section>', re.DOTALL)
PARA_RE = re.compile(r'<p>(.+?)</p>', re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')


def _clean(s):
    s = TAG_RE.sub('', s)
    s = html.unescape(s)
    s = re.sub(r'&ldquo;|&rdquo;', '"', s)
    return s.strip()


def _strip_existing_ts(title):
    return re.sub(r'^\[\d{1,2}(?::\d{2}){1,2}\]\s+', '', title)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html_path')
    ap.add_argument('txt_out')
    ap.add_argument('--timestamps', default='', help='1:0:00,2:0:46,...')
    args = ap.parse_args()

    with open(args.html_path) as f:
        doc = f.read()

    ts_map = {}
    if args.timestamps:
        for pair in args.timestamps.split(','):
            pair = pair.strip()
            if not pair:
                continue
            idx, ts = pair.split(':', 1)
            ts_map[int(idx)] = ts.strip()

    sections = SECTION_RE.findall(doc)
    if not sections:
        print('ERROR: no <section><h2>...</h2></section> found', file=sys.stderr)
        sys.exit(1)

    out = []
    for i, (raw_h2, body) in enumerate(sections, start=1):
        title = _strip_existing_ts(_clean(raw_h2))
        if i in ts_map:
            heading = f'[{ts_map[i]}] {title}'
        else:
            heading = title
        out.append('=' * 80)
        out.append(heading)
        out.append('')
        for p in PARA_RE.findall(body):
            text = _clean(p)
            if text:
                out.append(text)
                out.append('')

    with open(args.txt_out, 'w') as f:
        f.write('\n'.join(out).rstrip() + '\n')
    print(f'OK {args.txt_out} ({len(sections)} sections, {sum(1 for i in range(1, len(sections)+1) if i in ts_map)} with timestamp)')


if __name__ == '__main__':
    main()
