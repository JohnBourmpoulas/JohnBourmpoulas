import json
import math
import os
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

USER = "JohnBourmpoulas"
TOP_LANGUAGES = 7
EXCLUDED_REPOS = {USER}  # profile/README repo; add repo names here if desired

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{USER}-profile-telemetry",
    "X-GitHub-Api-Version": "2022-11-28",
}
token = os.environ.get("GH_TOKEN")
if token:
    headers["Authorization"] = "Bearer " + token


def get_json(url):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_repositories():
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USER}/repos"
            f"?per_page=100&page={page}&type=owner&sort=updated"
        )
        batch = get_json(url)
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def calculate_language_scores(repos):
    """Return balanced language scores across repositories.

    GitHub's language endpoint reports bytes. Summing raw bytes lets one very large
    repository dominate the profile. Instead, each repository contributes according
    to sqrt(repo_size), while languages inside that repository keep their real byte
    proportions. This still rewards substantial projects without allowing one huge
    codebase to overwhelm everything else.
    """
    scores = Counter()
    used_repos = 0

    for repo in repos:
        name = repo.get("name", "")
        if (
            repo.get("fork")
            or repo.get("archived")
            or repo.get("disabled")
            or name in EXCLUDED_REPOS
        ):
            continue

        try:
            languages = get_json(repo["languages_url"])
        except Exception as exc:
            print("Skipping", name, exc)
            continue

        repo_bytes = sum(languages.values())
        if not repo_bytes:
            continue

        # Sub-linear weighting: 100x more code => only 10x more influence.
        repo_weight = math.sqrt(repo_bytes)
        used_repos += 1
        print(f"Using {name}: {repo_bytes:,} bytes, weight={repo_weight:.1f}")

        for language, size in languages.items():
            scores[language] += (size / repo_bytes) * repo_weight

    print(f"Included {used_repos} repositories.")
    return scores


def render_svg(scores):
    total_score = sum(scores.values()) or 1
    languages = scores.most_common(TOP_LANGUAGES)

    width, top, row_h = 900, 78, 36
    height = top + max(len(languages), 1) * row_h + 24
    rows = []

    for index, (language, score) in enumerate(languages):
        y = top + index * row_h
        pct = (score / total_score) * 100
        bar_width = max(3, round(470 * pct / 100, 1))
        rows.extend([
            f'<text x="52" y="{y}" fill="#d8e2e8" font-family="monospace" font-size="13">{escape(language)}</text>',
            f'<text x="846" y="{y}" text-anchor="end" fill="#6d8590" font-family="monospace" font-size="11">{pct:.1f}%</text>',
            f'<rect x="215" y="{y-10}" width="470" height="4" rx="2" fill="#10212a"/>',
            f'<rect x="215" y="{y-10}" width="{bar_width}" height="4" rx="2" fill="#42def4"/>',
        ])

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="12" fill="#070b10" stroke="#16313a"/>'
        '<text x="52" y="36" fill="#67e8f9" font-family="monospace" font-size="10" letter-spacing="3">LANGUAGE TELEMETRY</text>'
        '<circle cx="838" cy="32" r="3" fill="#67e8f9"/>'
        '<text x="824" y="36" text-anchor="end" fill="#4d6872" font-family="monospace" font-size="9">LIVE</text>'
        + "".join(rows)
        + '</svg>'
    )
    Path("assets/languages.svg").write_text(svg, encoding="utf-8")

    print("Language telemetry updated:")
    for language, score in languages:
        print(f" - {language}: {(score / total_score) * 100:.1f}%")


def main():
    repos = fetch_repositories()
    scores = calculate_language_scores(repos)
    render_svg(scores)


if __name__ == "__main__":
    main()
