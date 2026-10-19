#!/usr/bin/env python3
"""Generate a recent public GitHub push activity SVG."""

import json
import os
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

username = os.environ["GH_USER"]
token = os.environ.get("GH_TOKEN", "")
url = f"https://api.github.com/users/{username}/events/public?per_page=100"

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-profile-activity-generator",
}

if token:
    headers["Authorization"] = f"Bearer {token}"

request = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(request, timeout=30) as response:
    events = json.load(response)

today = datetime.now(timezone.utc).date()
days = [today - timedelta(days=i) for i in range(27, -1, -1)]
counts = Counter()

for event in events:
    if event.get("type") != "PushEvent":
        continue

    day = event["created_at"][:10]
    payload = event.get("payload", {})
    commits = payload.get("commits")

    # Newer API payloads may omit individual commit details.
    count = len(commits) if isinstance(commits, list) else 1
    counts[day] += max(count, 1)

values = [counts.get(day.isoformat(), 0) for day in days]
maximum = max(values, default=0) or 1

width, height = 900, 210
bar_width, gap = 20, 10
start_x = 34
baseline = 155
chart_height = 100

bars = []
for i, value in enumerate(values):
    bar_height = value / maximum * chart_height
    x = start_x + i * (bar_width + gap)
    y = baseline - bar_height
    bars.append(
        f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" '
        f'height="{bar_height:.1f}" rx="3" fill="#38bdf8">'
        f'<title>{days[i].isoformat()}: {value} recorded commits</title>'
        '</rect>'
    )

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="12" fill="#0d1117"/>
<text x="34" y="35" font-family="monospace" font-size="18"
fill="#f0f6fc">Recent Public Push Activity</text>
<text x="34" y="55" font-family="monospace" font-size="11"
fill="#8b949e">Limited public events sample · not total contributions</text>
<line x1="34" y1="{baseline}" x2="866" y2="{baseline}"
stroke="#30363d"/>
{''.join(bars)}
<text x="34" y="185" font-family="monospace" font-size="12"
fill="#8b949e">{escape(days[0].isoformat())}</text>
<text x="760" y="185" font-family="monospace" font-size="12"
fill="#8b949e">{escape(today.isoformat())}</text>
</svg>"""

output = Path("assets/generated/activity.svg")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(svg, encoding="utf-8")
print(f"Generated {output}")
