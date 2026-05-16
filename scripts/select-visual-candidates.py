#!/usr/bin/env python3
import json
import re
from pathlib import Path

index = json.loads(Path("data/video-index.json").read_text())
clean_dir = Path("data/clean-transcripts")
notes_dir = Path("notes")
notes_dir.mkdir(exist_ok=True)

positive = {
    "how to": 30,
    "tutorial": 28,
    "demo": 24,
    "walkthrough": 24,
    "welcome": 14,
    "introduction": 14,
    "create": 16,
    "edit": 16,
    "set": 14,
    "connect": 14,
    "sync": 14,
    "profile": 12,
    "availability": 20,
    "invitee": 20,
    "invitation": 20,
    "meeting invitation": 24,
    "groups": 18,
    "public profile": 16,
    "public events": 14,
    "calendar": 12,
    "lotus notes": 12,
    "blackberry": 12,
    "iphone": 10,
    "web widget": 16,
    "personal scheduling page": 18,
    "logo and colors": 16,
    "favorite locations": 14,
    "time zone": 12,
    "default calendar": 12,
    "maximum and minimum": 14,
    "minimum proposed": 14,
}

negative = {
    "manifesto": -80,
    "talks": -35,
    "ceo": -18,
    "founder": -18,
    "scoble": -35,
    "don dodge": -35,
    "ed brill": -35,
    "helen crozier": -25,
    "geeks on a plane": -30,
    "giveaway": -20,
    "shout out": -30,
    "future of the calendar": -35,
    "transparency": -30,
    "ecosystem": -30,
    "semantic relationships": -30,
    "history": -20,
}

flow_tags = {
    "onboarding/core": ["welcome", "introduction", "what is", "what's tungle", "scheduling made easy", "tungle video"],
    "invitee experience": ["invitee", "invitations look"],
    "meeting creation": ["create meeting", "meeting invitation", "quickmeet", "edit meetings"],
    "availability rules": ["availability", "minimum proposed", "maximum and minimum", "number of times proposed"],
    "groups": ["group", "groups"],
    "calendar sync": ["sync", "calendar", "default calendar", "connect your calendar", "google account"],
    "profile/customization": ["profile", "logo", "colors", "favorite locations", "personal scheduling page", "web widget"],
    "mobile/clients": ["blackberry", "iphone", "lotus notes"],
    "sharing/events": ["share calendars", "public events"],
}

def transcript_word_count(video_id):
    p = clean_dir / f"{video_id}.txt"
    if not p.exists():
        return 0
    return len(re.findall(r"\w+", p.read_text(errors="ignore")))

def tags_for(text):
    tags = []
    low = text.lower()
    for tag, needles in flow_tags.items():
        if any(n in low for n in needles):
            tags.append(tag)
    return tags

ranked = []
for v in index:
    title = v.get("title") or ""
    desc = v.get("description") or ""
    video_id = v.get("id")
    low = f"{title}\n{desc}".lower()
    score = 0
    reasons = []
    for needle, weight in positive.items():
        if needle in low:
            score += weight
            reasons.append(f"+{weight} {needle}")
    for needle, weight in negative.items():
        if needle in low:
            score += weight
            reasons.append(f"{weight} {needle}")
    wc = transcript_word_count(video_id)
    if wc:
        score += 8
        reasons.append("+8 transcript")
    if wc > 1200:
        score += 5
        reasons.append("+5 substantial transcript")
    if any(x in low for x in ["how to", "tutorial", "demo"]):
        score += 15
        reasons.append("+15 explicit walkthrough form")

    flow = tags_for(low)
    is_selected = score >= 35 and bool(flow)
    ranked.append({
        "id": video_id,
        "title": title,
        "url": v.get("url") or f"https://www.youtube.com/watch?v={video_id}",
        "score": score,
        "selected": is_selected,
        "flow_tags": flow,
        "transcript_words": wc,
        "reasons": reasons,
    })

ranked.sort(key=lambda row: row["score"], reverse=True)
selected = [r for r in ranked if r["selected"]]
Path("data/visual-candidates.json").write_text(json.dumps({"selected": selected, "ranked": ranked}, indent=2, ensure_ascii=False) + "\n")

md = [
    "# Visual Candidates",
    "",
    "Videos likely to contain actual UI walkthroughs/screens worth frame extraction.",
    "",
    "Selection rule: explicit product/tutorial/demo language, product-flow tags, and no heavy manifesto/interview penalty.",
    "",
    f"Selected: **{len(selected)}** videos.",
    "",
    "## Pull frames",
    "",
    "```bash",
    "python3 scripts/pull-visual-candidate-frames.py",
    "```",
    "",
    "Frames land in `frames/<video-id>/` and are intentionally gitignored.",
    "",
    "## Selected UI walkthroughs",
    "",
]
for i, r in enumerate(selected, 1):
    md.extend([
        f"### {i}. {r['title']}",
        f"- Score: {r['score']}",
        f"- URL: {r['url']}",
        f"- Flow tags: {', '.join(r['flow_tags'])}",
        f"- Transcript words: {r['transcript_words']}",
        f"- Why: {'; '.join(r['reasons'][:8])}",
        f"- Frames: `frames/{r['id']}/`",
        "",
    ])

md.extend(["## Rejected / lower-confidence", ""])
for r in ranked[len(selected):len(selected)+30]:
    md.extend([f"- **{r['title']}** — score {r['score']}; tags: {', '.join(r['flow_tags']) or 'none'}; {r['url']}"])

Path("notes/visual-candidates.md").write_text("\n".join(md) + "\n")
print(f"selected {len(selected)} visual candidates")
