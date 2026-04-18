#!/usr/bin/env python3
"""
Infer [mm:ss] for each section heading in a formatted .txt by keyword
matching against the raw timestamped transcript.

Usage:
    python3 scripts/infer_section_timestamps.py \
        transcripts/<provider>/<vid>.txt \
        transcripts/<provider>/<vid>_en.txt

Prints comma-separated timestamps in section order, suitable for piping into
inject_section_timestamps.py:

    $ TS=$(python3 scripts/infer_section_timestamps.py raw.txt en.txt)
    $ python3 scripts/inject_section_timestamps.py en.txt "$TS"
"""
import re
import sys
from collections import Counter

STOPWORDS = set('''
a an and are as at be but by for from has have how if in into is it its
of on or the their them then there these this to was we will with you your
o a os as e do da de no na para por com um uma sua suas seu seus que se
foi era ser são estar está ter vai vão pode podem dos das nas nos este
esta isso isto também só mais mas como quando onde porque ou já bem ainda
'''.split())


def _tokenize(text):
    return [w.lower() for w in re.findall(r'[A-Za-zÀ-ú0-9]+', text) if len(w) > 2]


def _keywords(text, max_n=20):
    """Pick distinctive words: proper nouns, numbers, longer terms — minus stopwords."""
    toks = _tokenize(text)
    # Boost CamelCase / ALLCAPS / numbers in original casing
    boost = set()
    for w in re.findall(r'[A-ZÀ-Ú][A-ZÀ-Ú0-9]+|[A-Z][a-z]+[A-Z]\w+|\d+', text):
        boost.add(w.lower())
    # Filter stopwords + dedup, prioritize long + boosted
    filtered = [t for t in toks if t not in STOPWORDS]
    counts = Counter(filtered)
    scored = sorted(counts.items(), key=lambda kv: (-(kv[0] in boost) * 3 - kv[1] - len(kv[0]) / 5))
    return [w for w, _ in scored[:max_n]]


def _parse_raw(raw_path):
    """Return list of (timestamp_str, seconds, text) from a raw transcript with `mm:ss text` lines."""
    out = []
    with open(raw_path) as f:
        for line in f:
            m = re.match(r'^(\d{1,2}(?::\d{2}){1,2})\s+(.+)', line.strip())
            if not m:
                continue
            ts = m.group(1)
            parts = [int(p) for p in ts.split(':')]
            secs = parts[0] * 3600 + parts[1] * 60 + parts[2] if len(parts) == 3 else parts[0] * 60 + parts[1]
            out.append((ts, secs, m.group(2)))
    return out


def _parse_formatted(fmt_path):
    """Return list of (heading_title, body_text)."""
    with open(fmt_path) as f:
        lines = f.read().split('\n')
    sections = []
    state = 'wait_sep'
    title = None
    body = []
    for line in lines:
        s = line.strip()
        if s.startswith('=' * 10):
            if title is not None:
                sections.append((title, ' '.join(body).strip()))
                body = []
            state = 'expect_title'
            title = None
            continue
        if state == 'expect_title' and s:
            title = re.sub(r'^\[\d{1,2}(?::\d{2}){1,2}\]\s+', '', s)
            state = 'in_body'
            continue
        if state == 'in_body':
            body.append(s)
    if title is not None:
        sections.append((title, ' '.join(body).strip()))
    return sections


def _score_window(raw_segments, start_idx, window_size, keyword_set):
    """Sum keyword hits in [start_idx, start_idx+window_size) of raw text."""
    text = ' '.join(seg[2] for seg in raw_segments[start_idx:start_idx + window_size]).lower()
    return sum(text.count(kw) for kw in keyword_set)


def infer(raw_path, fmt_path, window_size=15):
    raw_segments = _parse_raw(raw_path)
    sections = _parse_formatted(fmt_path)
    if not raw_segments:
        print(f'ERROR: no timestamped lines in {raw_path}', file=sys.stderr)
        sys.exit(1)
    total = len(raw_segments)
    n_sec = len(sections)

    # For each section, search forward from the previous section's chosen index
    chosen_ts = []
    last_idx = 0
    for i, (title, body) in enumerate(sections):
        # Build keyword set from title + first ~400 chars of body
        sample = title + ' ' + body[:400]
        kws = set(_keywords(sample, max_n=15))
        if not kws:
            # Fallback: proportional
            target = int((i / n_sec) * total)
            chosen_ts.append(raw_segments[target][0])
            last_idx = target
            continue

        # Strict monotonicity: never search before last chosen index.
        # Search range end = generous slack past proportional position.
        proportional = int((i / n_sec) * total)
        search_start = last_idx + 1 if i > 0 else 0
        # Cap search end to prevent the heuristic from jumping into Q&A early on
        max_jump = max(80, total // n_sec * 3)
        search_end = min(max(proportional + max_jump, search_start + 30), total - window_size)
        if search_end <= search_start:
            search_end = min(search_start + 20, total - window_size)
            if search_end <= search_start:
                # Out of room — pin to last available segment
                chosen_ts.append(raw_segments[min(last_idx + 1, total - 1)][0])
                last_idx = min(last_idx + 1, total - 1)
                continue

        # Score = keyword hits − distance penalty from proportional position.
        # Penalty makes it prefer matches close to where this section "should" be.
        best_score = -1e9
        best_idx = search_start
        for idx in range(search_start, search_end):
            raw_score = _score_window(raw_segments, idx, window_size, kws)
            distance_penalty = abs(idx - proportional) / max(total / n_sec, 1) * 0.4
            score = raw_score - distance_penalty
            if score > best_score:
                best_score = score
                best_idx = idx

        chosen_ts.append(raw_segments[best_idx][0])
        last_idx = best_idx

    return chosen_ts, sections


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    timestamps, sections = infer(sys.argv[1], sys.argv[2])
    # Print TS list
    print(','.join(timestamps))
    # Also show the mapping on stderr for human review
    for ts, (title, _) in zip(timestamps, sections):
        print(f'  [{ts}] {title}', file=sys.stderr)


if __name__ == '__main__':
    main()
