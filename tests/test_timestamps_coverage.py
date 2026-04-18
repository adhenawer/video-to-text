"""Quality gate: every formatted transcript indexed in transcripts/index.json
must have [mm:ss] (or [hh:mm:ss]) on every section heading.

Posts marked with `"timestamps_backfilled": false` in index.json are skipped
(escape hatch for posts not yet backfilled). Removing the flag — or setting
it to true — re-enables enforcement.
"""
import json
import os
import re

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")
HEADING_TS_RE = re.compile(r'^\[\d{1,2}(?::\d{2}){1,2}\]\s+\S')


def _load_index():
    with open(INDEX_PATH) as f:
        return json.load(f)


def _section_titles(txt_path):
    """Return list of lines that look like section headings (first non-empty
    line right after a separator made of `=` chars)."""
    with open(txt_path) as f:
        lines = f.read().split("\n")
    titles = []
    expect_title = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("=" * 10):
            expect_title = True
            continue
        if expect_title and stripped:
            titles.append(stripped)
            expect_title = False
    return titles


def _entries_to_check():
    pairs = []
    for entry in _load_index():
        if entry.get("timestamps_backfilled") is False:
            continue
        vid = entry["video_id"]
        provider = entry["provider"]
        for suffix in ("_pt.txt", "_en.txt"):
            path = os.path.join(PROJECT_DIR, "transcripts", provider, f"{vid}{suffix}")
            if os.path.exists(path):
                pairs.append((entry["slug"], suffix, path))
    return pairs


@pytest.mark.parametrize("slug,suffix,path", _entries_to_check())
def test_all_section_headings_have_timestamp(slug, suffix, path):
    titles = _section_titles(path)
    assert titles, f"no sections found in {path}"
    bad = [t for t in titles if not HEADING_TS_RE.match(t)]
    assert not bad, (
        f"{slug}{suffix}: {len(bad)} section(s) missing [mm:ss] prefix:\n  - "
        + "\n  - ".join(bad[:5])
        + (f"\n  ...(+{len(bad)-5} more)" if len(bad) > 5 else "")
    )
