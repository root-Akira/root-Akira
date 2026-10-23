#!/usr/bin/env python3
"""Regenerate the 'On GitHub' section of README.md from the GitHub API.

Cards use GitHub's own OpenGraph images, so they always render
(no third-party stats service that can rate-limit or paywall).
"""
import json
import os
import re
import sys
import urllib.request

USER = "root-Akira"
README = "README.md"
MAX_REPOS = 8
EXCLUDE = {USER}  # skip the profile repo itself

START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"


def fetch_repos():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-readme-bot",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated",
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def card(repo):
    name = repo["name"]
    lang = repo.get("language") or "Code"
    stars = repo.get("stargazers_count", 0)
    meta = f"{lang} · ⭐ {stars}" if stars else lang
    return (
        '      <a href="{url}">\n'
        '        <img src="https://opengraph.githubassets.com/1/{user}/{repo}" '
        'width="100%" alt="{name}"/>\n'
        "      </a>\n"
        "      <br/><sub><b>{meta}</b></sub>\n"
    ).format(url=repo["html_url"], user=USER, repo=name, name=name, meta=meta)


def render(repos):
    repos = [r for r in repos if not r["fork"] and r["name"] not in EXCLUDE]
    repos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    repos = repos[:MAX_REPOS]

    rows = []
    for i in range(0, len(repos), 2):
        pair = repos[i : i + 2]
        cells = "".join(
            f'    <td width="50%" align="center">\n{card(r)}    </td>\n' for r in pair
        )
        if len(pair) == 1:
            cells += '    <td width="50%"></td>\n'
        rows.append("  <tr>\n" + cells + "  </tr>\n")

    table = "<table>\n" + "".join(rows) + "</table>"
    return f"{START}\n{table}\n{END}"


def main():
    if not os.path.exists(README):
        sys.exit(f"{README} not found")

    with open(README, encoding="utf-8") as f:
        text = f.read()

    if START not in text or END not in text:
        sys.exit("Markers not found in README.md")

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    new_text = pattern.sub(lambda _: render(fetch_repos()), text)

    if new_text == text:
        print("No changes.")
        return

    with open(README, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("README.md updated.")


if __name__ == "__main__":
    main()
