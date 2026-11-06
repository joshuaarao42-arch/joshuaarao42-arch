#!/usr/bin/env python3
"""Generate lightweight GitHub profile SVGs using the built-in Actions token."""
import json
import os
import urllib.error
import urllib.request
from html import escape

USERNAME = "joshuaarao42-arch"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
COLORS = ["#00D4FF", "#38BDF8", "#818CF8", "#A78BFA", "#34D399", "#FBBF24"]


def github_get(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-metrics",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"GitHub API request failed ({error.code}): {detail}") from error


def svg_start(width, height, title):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#101B35"/><stop offset="1" stop-color="#070B16"/></linearGradient></defs>',
        '<rect width="100%" height="100%" rx="18" fill="url(#bg)" stroke="#243653"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}.muted{fill:#94A3B8}.bright{fill:#EAF6FF}.accent{fill:#00D4FF}</style>',
    ]


def write_stats(user, repos):
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)
    metrics = [
        ("PUBLIC REPOSITORIES", user.get("public_repos", 0)),
        ("FOLLOWERS", user.get("followers", 0)),
        ("STARS EARNED", total_stars),
        ("FORKS", total_forks),
    ]
    parts = svg_start(900, 190, "GitHub profile statistics")
    parts.append('<text x="32" y="42" class="bright" font-size="20" font-weight="700">GITHUB OVERVIEW</text>')
    parts.append('<text x="32" y="64" class="muted" font-size="11">Live public profile data · refreshed automatically</text>')
    for index, (label, value) in enumerate(metrics):
        x = 32 + index * 218
        parts.append(f'<rect x="{x}" y="88" width="198" height="76" rx="12" fill="#0B1427" stroke="#263B5A"/>')
        parts.append(f'<text x="{x + 16}" y="116" class="muted" font-size="10" letter-spacing="1">{escape(label)}</text>')
        parts.append(f'<text x="{x + 16}" y="148" class="accent" font-size="27" font-weight="700">{value:,}</text>')
    parts.append("</svg>")
    with open("github-metrics.svg", "w", encoding="utf-8") as file:
        file.write("\n".join(parts))


def write_languages(language_totals):
    ranked = sorted(language_totals.items(), key=lambda item: item[1], reverse=True)[:6]
    total = sum(value for _, value in ranked) or 1
    parts = svg_start(900, 245, "Most used programming languages")
    parts.append('<text x="32" y="42" class="bright" font-size="20" font-weight="700">TOP LANGUAGES</text>')
    parts.append('<text x="32" y="64" class="muted" font-size="11">Based on language bytes across public repositories</text>')
    x, y, bar_width, bar_height, gap = 32, 92, 836, 13, 12
    current = x
    for index, (name, amount) in enumerate(ranked):
        width = bar_width * amount / total
        parts.append(f'<rect x="{current:.2f}" y="{y}" width="{max(width, 2):.2f}" height="{bar_height}" rx="6" fill="{COLORS[index]}"/>')
        current += width
    for index, (name, amount) in enumerate(ranked):
        row_y = 137 + index * 17
        percentage = amount / total * 100
        parts.append(f'<circle cx="40" cy="{row_y - 4}" r="4" fill="{COLORS[index]}"/>')
        parts.append(f'<text x="54" y="{row_y}" class="bright" font-size="12">{escape(name)}</text>')
        parts.append(f'<text x="866" y="{row_y}" class="muted" font-size="12" text-anchor="end">{percentage:.1f}%</text>')
    if not ranked:
        parts.append('<text x="32" y="130" class="muted" font-size="13">No public language data available yet.</text>')
    parts.append("</svg>")
    with open("github-languages.svg", "w", encoding="utf-8") as file:
        file.write("\n".join(parts))


def main():
    user = github_get(f"/users/{USERNAME}")
    repos = github_get(f"/users/{USERNAME}/repos?per_page=100&sort=updated&type=owner")
    language_totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        languages = github_get(f"/repos/{USERNAME}/{repo['name']}/languages")
        for language, amount in languages.items():
            language_totals[language] = language_totals.get(language, 0) + amount
    write_stats(user, repos)
    write_languages(language_totals)
    print(f"Generated profile SVGs from {len(repos)} public repositories.")


if __name__ == "__main__":
    main()
