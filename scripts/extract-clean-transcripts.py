#!/usr/bin/env python3
import re
from pathlib import Path

src_dir = Path("data/transcripts")
out_dir = Path("data/clean-transcripts")
out_dir.mkdir(parents=True, exist_ok=True)

seen_ids = set()
count = 0
for path in sorted(src_dir.glob("*.vtt")):
    m = re.search(r"-([A-Za-z0-9_-]{11})-", path.name)
    video_id = m.group(1) if m else path.stem
    # Prefer human-ish/original once; avoid duplicate en/en-orig copies.
    if video_id in seen_ids:
        continue
    seen_ids.add(video_id)

    lines = []
    last = None
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("WEBVTT") or "-->" in line or re.match(r"^\d+$", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and line != last:
            lines.append(line)
            last = line

    title = re.sub(r"\.en(-orig)?$", "", path.stem)
    out = out_dir / f"{video_id}.txt"
    out.write_text(f"# {title}\n\n" + "\n".join(lines) + "\n")
    count += 1

print(f"wrote {count} cleaned transcripts to {out_dir}")
