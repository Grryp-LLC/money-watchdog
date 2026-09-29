#!/usr/bin/env python3
"""Rebuild template/template-manifest.json from bot-profile.md, skills/, routines/, memories/."""
import json, re
from pathlib import Path
R = Path(__file__).resolve().parent.parent
strip = lambda t: re.sub(r'^---.*?---\n', '', t, flags=re.S).strip()
prof = (R / "bot-profile.md").read_text()
system_prompt = re.search(r"## System prompt / persona\n\n```\n(.*?)\n```", prof, re.S).group(1)
short = re.search(r"\*\*Short description\*\*[^|]*\|\s*(.*?)\s*\|\n", prof).group(1)
skills = []
for d in ["getting-started", "scan-inbox", "score-savings", "make-wanted-poster", "monthly-rap-sheet", "draft-cancellation"]:
    t = (R / "skills" / d / "SKILL.md").read_text()
    desc = " ".join(re.search(r"description: >-\n(.*?)\n---", t, re.S).group(1).split())
    skills.append({"name": d, "description": desc, "job": strip(t)})
rt = (R / "routines" / "ROUTINES.md").read_text()
routines = []
for name, cron in [("daily-money-scan", "7 8 * * *"), ("weekly-bounty-board", "37 8 * * 1"), ("monthly-rap-sheet", "17 9 1 * *")]:
    m = re.search(r"## \d\. " + name + r".*?\*\*Prompt:\*\*\n(.*?)(?=\n## |\Z)", rt, re.S)
    routines.append({"name": name, "schedule": cron, "timezone": "owner local",
                     "prompt": " ".join(l.strip().lstrip(">").strip() for l in m.group(1).splitlines() if l.strip())})
mem = [" ".join(x.split()) for x in re.split(r"\n- ", "\n" + (R / "memories" / "profile.md").read_text()) if x.strip()]
manifest = {
    "audience": "public",
    "name": "Money Watchdog",
    "title": "Sheriff of your inbox",
    "avatar": {"shape": "hex", "color": "yellow"},
    "description": short,
    "systemPrompt": system_prompt,
    "memories": {"profile": mem, "log": [" ".join((R / "memories" / "log.md").read_text().lstrip("- ").split())]},
    "skills": skills,
    "routines": routines,
    "routinesNote": "Created by getting-started in the new owner's timezone; specs in routines/ROUTINES.md.",
    "plugins": ["Gmail (marketplace connector; read-only use: thread search + thread read)"],
    "gettingStarted": "getting-started",
}
(R / "template" / "template-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print("wrote", R / "template" / "template-manifest.json", len(json.dumps(manifest)), "bytes")
