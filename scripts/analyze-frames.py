#!/usr/bin/env python3
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path.cwd()
FRAMES = ROOT / "frames"
OUT = ROOT / "data/frame-analysis"
NOTES = ROOT / "notes"
OUT.mkdir(parents=True, exist_ok=True)
NOTES.mkdir(exist_ok=True)

manifest = json.loads((ROOT / "data/visual-candidates.json").read_text())
selected = manifest["selected"]
by_id = {item["id"]: item for item in selected}

STOP = set("the a an and or to of in on for with your you me my is are be this that it click select from can will how tungle tungle.me".split())

def run(cmd):
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ocr_image(path: Path) -> str:
    proc = subprocess.run(["tesseract", str(path), "stdout", "--psm", "6"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    text = proc.stdout
    text = re.sub(r"\s+", " ", text).strip()
    return text

def avg_hash(path: Path) -> str:
    # 16x16 grayscale average hash via ffmpeg rawvideo. Good enough for duplicate-ish UI grouping.
    proc = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf", "scale=16:16,format=gray", "-f", "rawvideo", "-"])
    pixels = proc.stdout
    if not pixels:
        return "0" * 256
    avg = sum(pixels) / len(pixels)
    return "".join("1" if b >= avg else "0" for b in pixels)

def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))

def tokens(text: str):
    return set(t for t in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower()) if t not in STOP)

def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

frames = []
for item in selected:
    video_id = item["id"]
    for path in sorted((FRAMES / video_id).glob("*.jpg")):
        frame_no = int(path.stem)
        timestamp_seconds = (frame_no - 1) * 8
        frames.append({
            "video_id": video_id,
            "frame": path.name,
            "frame_path": str(path.relative_to(ROOT)),
            "timestamp_seconds": timestamp_seconds,
            "timestamp": f"{timestamp_seconds//60:02d}:{timestamp_seconds%60:02d}",
            "title": item["title"],
            "url": item["url"],
            "flow_tags": item["flow_tags"],
        })

ocr_cache_path = OUT / "frame-ocr.json"
if ocr_cache_path.exists():
    ocr_rows = json.loads(ocr_cache_path.read_text())
    cached = {row["frame_path"]: row for row in ocr_rows}
else:
    cached = {}

ocr_rows = []
for i, frame in enumerate(frames, 1):
    if frame["frame_path"] in cached:
        row = cached[frame["frame_path"]]
    else:
        path = ROOT / frame["frame_path"]
        text = ocr_image(path)
        row = {**frame, "ocr_text": text, "ocr_tokens": sorted(tokens(text)), "avg_hash": avg_hash(path)}
        print(f"OCR {i}/{len(frames)} {frame['frame_path']}")
    ocr_rows.append(row)

ocr_cache_path.write_text(json.dumps(ocr_rows, indent=2, ensure_ascii=False) + "\n")

# Group similar consecutive UI states within each video. This favors flow-state segmentation over global dedupe.
groups = []
for video_id, rows in defaultdict(list, {vid: [r for r in ocr_rows if r["video_id"] == vid] for vid in by_id}).items():
    rows = sorted(rows, key=lambda r: r["timestamp_seconds"])
    current = None
    for row in rows:
        row_tokens = set(row.get("ocr_tokens", []))
        if current is None:
            current = {"video_id": video_id, "title": row["title"], "url": row["url"], "flow_tags": row["flow_tags"], "frames": [row]}
            continue
        prev = current["frames"][-1]
        sim_text = jaccard(set(prev.get("ocr_tokens", [])), row_tokens)
        sim_hash = 1 - (hamming(prev["avg_hash"], row["avg_hash"]) / len(prev["avg_hash"]))
        # Same state if visually very close or OCR text remains substantially same.
        if sim_hash >= 0.88 or sim_text >= 0.55:
            current["frames"].append(row)
        else:
            groups.append(current)
            current = {"video_id": video_id, "title": row["title"], "url": row["url"], "flow_tags": row["flow_tags"], "frames": [row]}
    if current:
        groups.append(current)

state_rows = []
for idx, g in enumerate(groups, 1):
    all_text = " ".join(f.get("ocr_text", "") for f in g["frames"])
    words = tokens(all_text)
    rep = max(g["frames"], key=lambda f: len(f.get("ocr_text", "")))
    start = g["frames"][0]["timestamp"]
    end = g["frames"][-1]["timestamp"]
    state_rows.append({
        "state_id": f"S{idx:03d}",
        "video_id": g["video_id"],
        "title": g["title"],
        "url": g["url"],
        "flow_tags": g["flow_tags"],
        "start": start,
        "end": end,
        "frame_count": len(g["frames"]),
        "representative_frame": rep["frame_path"],
        "ocr_excerpt": rep.get("ocr_text", "")[:500],
        "keywords": sorted(words)[:30],
        "frames": [f["frame_path"] for f in g["frames"]],
    })

(OUT / "ui-state-groups.json").write_text(json.dumps(state_rows, indent=2, ensure_ascii=False) + "\n")

flow_to_states = defaultdict(list)
for s in state_rows:
    for tag in s["flow_tags"] or ["uncategorized"]:
        flow_to_states[tag].append(s)

board = ["# UI Evidence Board", "", "OCR + rough UI-state grouping from selected Tungle walkthrough frames.", "", "## Summary", "", f"- Source videos: {len(selected)}", f"- Frames OCR'd: {len(ocr_rows)}", f"- Grouped UI states: {len(state_rows)}", "- Grouping method: consecutive frames by average visual hash similarity and OCR token overlap.", "- Caveat: OCR is noisy; every product claim still needs human screenshot review before becoming spec.", ""]
for flow, states in sorted(flow_to_states.items()):
    board += [f"## {flow}", ""]
    for s in states:
        excerpt = s["ocr_excerpt"] or "_No readable OCR text; inspect frame visually._"
        board += [
            f"### {s['state_id']} — {s['title']} [{s['start']}–{s['end']}]",
            f"- Video: {s['url']}",
            f"- Representative frame: `{s['representative_frame']}`",
            f"- Frames in state: {s['frame_count']}",
            f"- OCR excerpt: {excerpt}",
            f"- Keywords: {', '.join(s['keywords'][:18]) or 'none'}",
            "",
        ]

(NOTES / "ui-evidence-board.md").write_text("\n".join(board) + "\n")

flows = ["# Reconstructed Flows", "", "First-pass reconstruction from selected visual walkthrough titles, flow tags, OCR, and UI-state groups. Treat as evidence-indexed working notes, not final spec.", ""]
for flow, states in sorted(flow_to_states.items()):
    flows += [f"## {flow}", "", "### Evidence sequence", ""]
    by_video = defaultdict(list)
    for s in states:
        by_video[s["title"]].append(s)
    for title, ss in by_video.items():
        flows.append(f"- **{title}**")
        for s in sorted(ss, key=lambda x: (x["video_id"], x["start"])):
            snippet = s["ocr_excerpt"] or "visual-only/no OCR"
            snippet = snippet[:160]
            flows.append(f"  - `{s['state_id']}` `{s['start']}–{s['end']}` `{s['representative_frame']}` — {snippet}")
    flows += ["", "### Rebuild notes", "", "- needs_human_review: confirm screens and exact behavior against representative frames.", "- needs_source: promote only verified UI behavior into a PRD/spec.", ""]

(NOTES / "reconstructed-flows.md").write_text("\n".join(flows) + "\n")
print(f"wrote {len(ocr_rows)} OCR rows, {len(state_rows)} UI state groups")
