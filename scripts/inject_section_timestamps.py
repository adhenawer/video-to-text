#!/usr/bin/env python3
"""
Inject [mm:ss] prefix into section headings of an existing formatted .txt.

Usage:
    python3 scripts/inject_section_timestamps.py \
        transcripts/<provider>/<vid>_pt.txt \
        "0:00,0:46,1:50,..."

Pass timestamps in the SAME order as sections appear in the file. Length
must match section count. Existing [mm:ss] prefixes are stripped first.
"""
import re
import sys


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    timestamps = [t.strip() for t in sys.argv[2].split(',') if t.strip()]

    with open(path) as f:
        lines = f.read().split('\n')

    out = []
    prev_was_sep = False
    section_idx = 0
    for line in lines:
        s = line.strip()
        if s.startswith('=' * 10):
            prev_was_sep = True
            out.append(line)
            continue
        if prev_was_sep and s:
            prev_was_sep = False
            if section_idx >= len(timestamps):
                print(f'ERROR: more sections than timestamps (section {section_idx+1})', file=sys.stderr)
                sys.exit(1)
            stripped_title = re.sub(r'^\[\d{1,2}(?::\d{2}){1,2}\]\s+', '', s)
            out.append(f'[{timestamps[section_idx]}] {stripped_title}')
            section_idx += 1
            continue
        out.append(line)

    if section_idx != len(timestamps):
        print(f'WARN: {section_idx} sections in file, {len(timestamps)} timestamps provided', file=sys.stderr)

    with open(path, 'w') as f:
        f.write('\n'.join(out))
    print(f'OK {path} ({section_idx} sections marked)')


if __name__ == '__main__':
    main()
