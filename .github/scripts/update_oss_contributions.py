"""Regenerates the merged/in-review contribution tables in README.md
between the OSS-CONTRIB markers, from live GitHub PR search results."""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USERNAME = os.environ["USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
README_PATH = os.environ.get("README_PATH", "README.md")

API_ROOT = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": USERNAME,
}

MERGED_COLOR = "FF8C00"
REVIEW_COLOR = "7209B7"
MAX_MERGED_ROWS = 15
MAX_REVIEW_ROWS = 8


def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def search_prs(state):
    query = f"author:{USERNAME} is:pr is:{state}"
    url = f"{API_ROOT}/search/issues?q={urllib.parse.quote(query)}&per_page=100"
    return api_get(url).get("items", [])


def group_by_external_repo(items):
    groups = {}
    for item in items:
        owner, repo = item["repository_url"].rsplit("/", 2)[-2:]
        if owner.lower() == USERNAME.lower():
            continue
        key = f"{owner}/{repo}"
        groups.setdefault(key, {"owner": owner, "repo": repo, "prs": []})["prs"].append(item)
    return groups


def fetch_stars(owner, repo, cache):
    key = f"{owner}/{repo}"
    if key not in cache:
        cache[key] = api_get(f"{API_ROOT}/repos/{owner}/{repo}").get("stargazers_count", 0)
        time.sleep(0.3)
    return cache[key]


def display_name(repo):
    return " ".join(w.capitalize() for w in re.split(r"[-_]", repo))


def star_badge(owner, repo, color):
    label = urllib.parse.quote("⭐")
    return (f'<img src="https://img.shields.io/github/stars/{owner}/{repo}'
            f'?style=flat-square&label={label}&labelColor=1a012b&color={color}" alt="stars" />')


def rank_groups(groups, star_cache):
    ranked = list(groups.values())
    for g in ranked:
        g["stars"] = fetch_stars(g["owner"], g["repo"], star_cache)
    ranked.sort(key=lambda g: g["stars"], reverse=True)
    return ranked


def build_merged_table(ranked):
    total_prs = sum(len(g["prs"]) for g in ranked)
    combined_stars = sum(g["stars"] for g in ranked)
    top_names = [display_name(g["repo"]) for g in ranked[:3]]

    stars_text = f"{combined_stars // 1000}k+" if combined_stars >= 1000 else str(combined_stars)
    summary = (
        f'**{total_prs} merged PR{"s" if total_prs != 1 else ""} across '
        f'{len(ranked)} project{"s" if len(ranked) != 1 else ""}** with a combined '
        f"⭐ {stars_text}"
    )
    if top_names:
        summary += f' — including {", ".join(top_names)}.'

    lines = [summary, "", "| Project | Stars | What I shipped |", "|---|---|---|"]
    for g in ranked[:MAX_MERGED_ROWS]:
        owner, repo = g["owner"], g["repo"]
        prs = sorted(g["prs"], key=lambda p: p["number"], reverse=True)
        latest = prs[0]
        badge = star_badge(owner, repo, MERGED_COLOR)
        if len(prs) == 1:
            desc = f'{latest["title"]} — [merged PR ↗]({latest["html_url"]})'
        else:
            search_url = (
                f"https://github.com/{owner}/{repo}/pulls?q="
                + urllib.parse.quote(f"is:pr author:{USERNAME} is:merged")
            )
            desc = f'{latest["title"]} — [{len(prs)} merged PRs ↗]({search_url})'
        lines.append(f'| **[{owner}/{repo}](https://github.com/{owner}/{repo})** | {badge} | {desc} |')
    return "\n".join(lines)


def build_review_section(ranked):
    total_prs = sum(len(g["prs"]) for g in ranked)
    top_names = [display_name(g["repo"]) for g in ranked[:4]]
    names_text = ", ".join(top_names)

    lines = [
        f"<details>",
        f'<summary>🔭 Also currently in review across {names_text} & more ({total_prs} open PRs)</summary>',
        "<br/>",
        "",
        "| Project | Stars | Pending PR |",
        "|---|---|---|",
    ]
    for g in ranked[:MAX_REVIEW_ROWS]:
        owner, repo = g["owner"], g["repo"]
        prs = sorted(g["prs"], key=lambda p: p["number"], reverse=True)
        latest = prs[0]
        badge = star_badge(owner, repo, REVIEW_COLOR)
        if len(prs) == 1:
            desc = f'{latest["title"]} — [review ↗]({latest["html_url"]})'
        else:
            search_url = (
                f"https://github.com/{owner}/{repo}/pulls?q="
                + urllib.parse.quote(f"is:pr author:{USERNAME} is:open")
            )
            desc = f'{len(prs)} open PRs — [review ↗]({search_url})'
        lines.append(f'| **[{owner}/{repo}](https://github.com/{owner}/{repo})** | {badge} | {desc} |')
    lines += ["", "</details>"]
    return "\n".join(lines)


def main():
    star_cache = {}

    merged_items = search_prs("merged")
    open_items = search_prs("open")

    merged_ranked = rank_groups(group_by_external_repo(merged_items), star_cache)
    open_ranked = rank_groups(group_by_external_repo(open_items), star_cache)

    block = build_merged_table(merged_ranked)
    if open_ranked:
        block += "\n\n" + build_review_section(open_ranked)

    with open(README_PATH, encoding="utf-8") as f:
        readme = f.read()

    pattern = re.compile(
        r"<!-- OSS-CONTRIB:START -->.*?<!-- OSS-CONTRIB:END -->", re.DOTALL
    )
    if not pattern.search(readme):
        print("OSS-CONTRIB markers not found in README.md", file=sys.stderr)
        sys.exit(1)

    replacement = f"<!-- OSS-CONTRIB:START -->\n{block}\n<!-- OSS-CONTRIB:END -->"
    new_readme = pattern.sub(lambda _: replacement, readme, count=1)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)


if __name__ == "__main__":
    main()
