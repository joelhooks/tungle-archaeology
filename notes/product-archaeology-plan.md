# Product Archaeology Plan

## First pass

1. Pull channel metadata and captions without downloading videos.
2. Rank videos likely to contain product walkthroughs.
3. Review the top 10 by transcript and title.
4. Pick visual walkthrough candidates for frame extraction.

## Later visual pass

- Download only selected videos or clips.
- Extract scene-change frames with ffmpeg.
- OCR UI screenshots.
- Group evidence by flow: onboarding, invite, availability, group scheduling, calendar sync, confirmations.

## Evidence rules

- Every feature claim needs a source video/timestamp/screenshot.
- Unknown behavior gets marked `needs_evidence`, not hallucinated.
