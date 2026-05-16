#!/usr/bin/env python3
import json, re
from pathlib import Path

index_path = Path("data/video-index.json")
transcript_dir = Path("data/transcripts")
notes_dir = Path("notes")
notes_dir.mkdir(exist_ok=True)

if not index_path.exists():
    raise SystemExit("Missing data/video-index.json. Run ./scripts/fetch-channel-metadata.sh first.")

videos = json.loads(index_path.read_text())
keywords = {
    "walkthrough": 8,
    "demo": 8,
    "tour": 7,
    "how to": 5,
    "schedule": 5,
    "meeting": 5,
    "calendar": 5,
    "availability": 6,
    "invite": 5,
    "group": 5,
    "iphone": 3,
    "blackberry": 3,
    "outlook": 3,
    "google calendar": 3,
    "sync": 4,
}

def clean_vtt(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if not line or line.startswith("WEBVTT") or "-->" in line or re.match(r"^\d+$", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        lines.append(line.strip())
    return " ".join(lines)

transcripts = {}
for path in transcript_dir.glob("*.vtt"):
    m = re.search(r"-([A-Za-z0-9_-]{11})-", path.name)
    if m:
        transcripts[m.group(1)] = clean_vtt(path.read_text(errors="ignore"))

ranked = []
for v in videos:
    title = v.get("title") or ""
    desc = v.get("description") or ""
    text = " ".join([title, desc, transcripts.get(v.get("id"), "")]).lower()
    score = 0
    hits = []
    for kw, weight in keywords.items():
        if kw in text:
            count = text.count(kw)
            score += weight * min(count, 5)
            hits.append(kw)
    if transcripts.get(v.get("id")):
        score += 10
    ranked.append({**v, "score": score, "keyword_hits": sorted(set(hits)), "has_transcript": v.get("id") in transcripts})

ranked.sort(key=lambda x: x["score"], reverse=True)
Path("data/ranked-candidates.json").write_text(json.dumps(ranked, indent=2, ensure_ascii=False) + "\n")

md = ["# Tungle Transcript Mining Candidates", "", "Ranked by product-walkthrough language and transcript availability.", ""]
for i, v in enumerate(ranked[:30], 1):
    url = v.get("url") or (f"https://www.youtube.com/watch?v={v['id']}" if v.get("id") else "")
    md.append(f"## {i}. {v.get('title', 'Untitled')}")
    md.append(f"- Score: {v['score']}")
    md.append(f"- Transcript: {'yes' if v['has_transcript'] else 'no'}")
    md.append(f"- Hits: {', '.join(v['keyword_hits']) or 'none'}")
    md.append(f"- URL: {url}")
    md.append("")
notes_dir.joinpath("transcript-candidates.md").write_text("\n".join(md))
print("wrote data/ranked-candidates.json and notes/transcript-candidates.md")
