#!/usr/bin/env bash
set -euo pipefail

CHANNEL_URL="${1:-https://www.youtube.com/@TungleRocks/videos}"
mkdir -p data/raw data/transcripts

# Flat metadata first: cheap, fast, good for ranking candidates.
yt-dlp \
  --flat-playlist \
  --dump-json \
  "$CHANNEL_URL" \
  > data/raw/channel-videos.jsonl

python3 scripts/jsonl-to-index.py data/raw/channel-videos.jsonl data/video-index.json

# Transcript/subtitle pull. This avoids video downloads.
# yt-dlp writes one subtitle file per video where captions exist.
yt-dlp \
  --skip-download \
  --write-subs \
  --write-auto-subs \
  --sub-langs "en.*" \
  --sub-format vtt \
  --ignore-errors \
  --output "data/transcripts/%(upload_date)s-%(id)s-%(title).120B.%(ext)s" \
  "$CHANNEL_URL"
