import json, os, urllib.request
from collections import Counter
from pathlib import Path
from html import escape

USER = "JohnBourmpoulas"
headers = {"Accept":"application/vnd.github+json","User-Agent":"profile-telemetry"}
token = os.environ.get("GH_TOKEN")
if token:
    headers["Authorization"] = "Bearer " + token

def get(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

repos, page = [], 1
while True:
    batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
    repos += batch
    if len(batch) < 100:
        break
    page += 1

totals = Counter()
for repo in repos:
    if not repo.get("fork"):
        try:
            totals.update(get(repo["languages_url"]))
        except Exception as e:
            print("Skipping", repo["name"], e)

total = sum(totals.values()) or 1
langs = totals.most_common(7)
width, top, row_h = 900, 78, 36
height = top + max(len(langs), 1) * row_h + 24
rows = []

for i, (lang, size) in enumerate(langs):
    y = top + i * row_h
    pct = size / total * 100
    bw = max(3, round(470 * pct / 100, 1))
    rows.append(f'<text x="52" y="{y}" fill="#d8e2e8" font-family="monospace" font-size="13">{escape(lang)}</text>')
    rows.append(f'<text x="846" y="{y}" text-anchor="end" fill="#6d8590" font-family="monospace" font-size="11">{pct:.1f}%</text>')
    rows.append(f'<rect x="215" y="{y-10}" width="470" height="4" rx="2" fill="#10212a"/>')
    rows.append(f'<rect x="215" y="{y-10}" width="{bw}" height="4" rx="2" fill="#42def4"/>')

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    f'<rect width="{width}" height="{height}" rx="12" fill="#070b10" stroke="#16313a"/>'
    '<text x="52" y="36" fill="#67e8f9" font-family="monospace" font-size="10" letter-spacing="3">LANGUAGE TELEMETRY</text>'
    '<circle cx="838" cy="32" r="3" fill="#67e8f9"/>'
    '<text x="824" y="36" text-anchor="end" fill="#4d6872" font-family="monospace" font-size="9">LIVE</text>'
    + "".join(rows) + '</svg>'
)
Path("assets/languages.svg").write_text(svg, encoding="utf-8")
print("Updated assets/languages.svg")
