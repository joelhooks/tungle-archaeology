#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

root = Path.cwd()
manifest_path = root / "data/visual-candidates.json"
if not manifest_path.exists():
    raise SystemExit("Missing data/visual-candidates.json. Run scripts/select-visual-candidates.py first.")

manifest = json.loads(manifest_path.read_text())
selected = manifest["selected"]
video_dir = root / "data/video-cache"
frames_dir = root / "frames"
video_dir.mkdir(parents=True, exist_ok=True)
frames_dir.mkdir(parents=True, exist_ok=True)

# Pull frames only for selected visual candidates. Defaults are intentionally sparse:
# one frame every 8 seconds plus scene-change-ish filtering would be overkill for pass 1.
for item in selected:
    video_id = item["id"]
    url = item["url"] or f"https://www.youtube.com/watch?v={video_id}"
    out_template = str(video_dir / f"{video_id}.%(ext)s")
    target_dir = frames_dir / video_id
    target_dir.mkdir(parents=True, exist_ok=True)

    existing_frames = list(target_dir.glob("*.jpg"))
    if existing_frames:
        print(f"skip frames {video_id}: {len(existing_frames)} already exist")
        continue

    print(f"download selected video {video_id}: {item['title']}")
    subprocess.run([
        "yt-dlp",
        "--no-playlist",
        "--format", "18/best[height<=720]/best",
        "--merge-output-format", "mp4",
        "--output", out_template,
        url,
    ], check=True)

    video_files = sorted(video_dir.glob(f"{video_id}.*"))
    if not video_files:
        raise SystemExit(f"Downloaded file missing for {video_id}")
    video_file = video_files[0]

    print(f"extract frames {video_id}")
    subprocess.run([
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", str(video_file),
        "-vf", "fps=1/8,scale=1280:-1",
        "-q:v", "3",
        str(target_dir / "%05d.jpg"),
    ], check=True)

print("done")
