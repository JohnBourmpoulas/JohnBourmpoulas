import json
import os
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

USER = "JohnBourmpoulas"
PROFILE_REPO = USER
MAX_LANGUAGES = 7

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "JohnBourmpoulas-profile-telemetry",
    "X-GitHub-Api-Version": "2022-11-28",
}

token = os.environ.get("GH_TOKEN")
if token:
    headers["Authorization"] = "Bearer " + token


def get_json(url):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


# Fetch all public repositories owned by the profile.
repos = []
page = 1
while True:
    url = (
        f"https://api.github.com/users/{USER}/repos"
        f"?per_page=100&page={page}&type=owner&sort=updated"
    )
    batch = get_json(url)
    if not batch:
        break
    repos.extend(batch)
    if len(batch) < 100:
        break
    page += 1

# One project = one vote for its GitHub primary language.
# We intentionally do NOT sum language bytes/lines.
project_counts = Counter()
counted_repos = []

for repo in repos:
    if repo.get("fork") or repo.get("archived") or repo.get("disabled"):
        continue
    if repo.get("name") == PROFILE_REPO:
        continue

    language = repo.get("language")
    if not language:
        continue

    project_counts[language] += 1
    counted_repos.append((repo.get("name", "unknown"), language))

project_total = sum(project_counts.values()) or 1
languages = project_counts.most_common(MAX_LANGUAGES)

width = 900
top = 78
row_h = 36
height = top + max(len(languages), 1) * row_h + 24
rows = []

for index, (language, project_count) in enumerate(languages):
    y = top + index * row_h
    pct = (project_count / project_total) * 100
    bar_width = max(3, round(470 * pct / 100, 1))

    rows.append(
        f'<text x="52" y="{y}" fill="#d8e2e8" '
        f'font-family="monospace" font-size="13">{escape(language)}</text>'
    )
    rows.append(
        f'<text x="846" y="{y}" text-anchor="end" fill="#6d8590" '
        f'font-family="monospace" font-size="11">{project_count} proj · {pct:.1f}%</text>'
    )
    rows.append(
        f'<rect x="215" y="{y - 10}" width="470" height="4" '
        f'rx="2" fill="#10212a"/>'
    )
    rows.append(
        f'<rect x="215" y="{y - 10}" width="{bar_width}" height="4" '
        f'rx="2" fill="#42def4"/>'
    )

if not languages:
    rows.append(
        '<text x="52" y="78" fill="#6d8590" font-family="monospace" '
        'font-size="12">No language-tagged projects found.</text>'
    )

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">'
    f'<rect width="{width}" height="{height}" rx="12" fill="#070b10" stroke="#16313a"/>'
    '<text x="52" y="36" fill="#67e8f9" font-family="monospace" '
    'font-size="10" letter-spacing="3">LANGUAGE TELEMETRY · PROJECT COUNT</text>'
    '<circle cx="838" cy="32" r="3" fill="#67e8f9"/>'
    '<text x="824" y="36" text-anchor="end" fill="#4d6872" '
    'font-family="monospace" font-size="9">LIVE</text>'
    + "".join(rows)
    + '</svg>'
)

Path("assets/languages.svg").write_text(svg, encoding="utf-8")

print(f"Counted {len(counted_repos)} projects:")
for repo_name, language in sorted(counted_repos):
    print(f" - {repo_name}: {language}")

print("\nLanguage telemetry:")
for language, project_count in languages:
    pct = (project_count / project_total) * 100
    print(f" - {language}: {project_count} project(s) ({pct:.1f}%)")
