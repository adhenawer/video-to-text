#!/usr/bin/env python3
"""Add references summary to transcripts/index.json for each entry."""
import json
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")


def main():
    with open(INDEX_PATH) as f:
        index = json.load(f)

    for entry in index:
        vid_id = entry["video_id"]
        provider = entry["provider"]
        refs_path = os.path.join(
            PROJECT_DIR, "transcripts", provider, f"{vid_id}.references.json"
        )
        if not os.path.exists(refs_path):
            entry["references"] = None
            continue
        with open(refs_path) as f:
            refs = json.load(f)
        entry["references"] = {
            "path": f"transcripts/{provider}/{vid_id}.references.json",
            "counts": {
                "books": len(refs.get("books", [])),
                "tools": len(refs.get("tools", [])),
                "papers": len(refs.get("papers", [])),
                "people": len(refs.get("people", [])),
                "concepts": len(refs.get("concepts", [])),
                "companies": len(refs.get("companies", [])),
                "related_posts": len(refs.get("related_posts", [])),
            },
            "total": sum(len(refs.get(k, [])) for k in
                         ["books","tools","papers","people","concepts","companies"]),
        }

    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    total_refs = sum(e.get("references", {}).get("total", 0) or 0 for e in index)
    print(f"Updated {len(index)} entries with references summary")
    print(f"Total refs across site: {total_refs}")


if __name__ == "__main__":
    main()
