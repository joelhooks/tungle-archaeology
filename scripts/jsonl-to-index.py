#!/usr/bin/env python3
import json, sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
items = []
for line in src.read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    items.append({
        "id": row.get("id"),
        "title": row.get("title"),
        "url": row.get("url") or row.get("webpage_url"),
        "duration": row.get("duration"),
        "view_count": row.get("view_count"),
        "upload_date": row.get("upload_date"),
        "description": row.get("description"),
    })

dst.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {len(items)} videos to {dst}")
