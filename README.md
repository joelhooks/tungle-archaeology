# Tungle Archaeology

Product archaeology for the old Tungle scheduling product, starting from public YouTube walkthroughs.

Goal: collect metadata/transcripts, identify the best visual walkthrough candidates, then reconstruct flows and product behavior from evidence.

## Workflow

```bash
./scripts/fetch-channel-metadata.sh
python3 scripts/rank-transcript-candidates.py
```

Outputs land in `data/` and derived notes in `notes/`.
