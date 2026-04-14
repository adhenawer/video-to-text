#!/usr/bin/env python3
"""Build Map of Content JSON for the graph visualization.

Reads transcripts/index.json (nodes) and each {id}.references.json
(edges via related_posts[].slug_pt). Writes docs/data/moc.json.
"""
import json
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")
OUT_DIR = os.path.join(PROJECT_DIR, "docs", "data")
OUT_PATH = os.path.join(OUT_DIR, "moc.json")


def _short_title(title: str, subtitle: str) -> str:
    t = (title or "").strip()
    if ":" in t and len(t) > 42:
        t = t.split(":", 1)[0].strip()
    if " — " in t and len(t) > 42:
        t = t.split(" — ", 1)[0].strip()
    if len(t) > 48:
        t = t[:46].rstrip() + "…"
    return t


def main() -> None:
    with open(INDEX_PATH) as f:
        index = json.load(f)

    nodes = []
    slug_set = set()
    for entry in index:
        slug = entry["slug"]
        if slug in slug_set:
            continue
        slug_set.add(slug)
        nodes.append({
            "id": slug,
            "title": _short_title(entry.get("title", slug), entry.get("subtitle", "")),
            "subtitle": entry.get("subtitle", ""),
            "url_pt": f"posts/pt_br/{slug}.html",
            "url_en": f"posts/original/{entry.get('slug_en', slug)}.html",
            "refs_total": (entry.get("references") or {}).get("total", 0),
        })

    edge_seen = set()
    edges = []
    for entry in index:
        slug = entry["slug"]
        refs_info = entry.get("references") or {}
        refs_path = refs_info.get("path")
        if not refs_path:
            continue
        abs_refs = os.path.join(PROJECT_DIR, refs_path)
        if not os.path.exists(abs_refs):
            continue
        with open(abs_refs) as f:
            refs = json.load(f)
        for rel in refs.get("related_posts") or []:
            target = rel.get("slug_pt")
            if not target or target == slug or target not in slug_set:
                continue
            key = tuple(sorted([slug, target]))
            if key in edge_seen:
                continue
            edge_seen.add(key)
            edges.append({"source": key[0], "target": key[1]})

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {"nodes": nodes, "edges": edges}
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"moc.json: {len(nodes)} nodes, {len(edges)} edges → {OUT_PATH}")


if __name__ == "__main__":
    main()
