"""Refreshes only the lead summary sentence of the merged-contributions
section (PR count, project count, combined stars) between the OSS-CONTRIB
markers, by recomputing those numbers from the table rows you've already
written. It never adds, removes, or reorders a row, never rewrites a
description, and never touches the "currently in review" section — those
stay exactly as hand-curated. This keeps the summary numbers from silently
going stale next to the live star badges, without reintroducing the risk of
auto-generated text overwriting curated wording."""

import json
import os
import re
import time
import urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
README_PATH = os.environ.get("README_PATH", "README.md")

API_ROOT = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "oss-contributions-summary-refresh",
}

MARKER_START = "<!-- OSS-CONTRIB:START -->"
MARKER_END = "<!-- OSS-CONTRIB:END -->"

ROW_PATTERN = re.compile(r"^\| \*\*\[([\w.\-]+/[\w.\-]+)\]\(https://github\.com/[\w.\-]+/[\w.\-]+\)\*\* \|.*\|\s*$")
COUNT_PATTERN = re.compile(r"\[(\d+) merged PRs")
LEAD_PATTERN = re.compile(r"\*\*\d[\d,]* merged PRs? across \d[\d,]* projects?\*\* with a combined ⭐ [\d,]+k?\+?")


def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_stars(owner, repo):
    return api_get(f"{API_ROOT}/repos/{owner}/{repo}").get("stargazers_count", 0)


def pluralize(n, singular):
    return singular if n == 1 else singular + "s"


def main():
    with open(README_PATH, encoding="utf-8") as f:
        readme = f.read()

    start = readme.index(MARKER_START)
    end = readme.index(MARKER_END) + len(MARKER_END)
    block = readme[start:end]

    # Only the merged-contributions table (everything before the "in review"
    # <details> section) feeds these numbers.
    merged_part = block.split("<details>", 1)[0]

    total_prs = 0
    combined_stars = 0
    project_count = 0
    for line in merged_part.splitlines():
        match = ROW_PATTERN.match(line)
        if not match:
            continue
        project_count += 1
        count_match = COUNT_PATTERN.search(line)
        total_prs += int(count_match.group(1)) if count_match else 1

        owner, repo = match.group(1).split("/", 1)
        combined_stars += fetch_stars(owner, repo)
        time.sleep(0.3)

    stars_text = f"{combined_stars // 1000}k+" if combined_stars >= 1000 else str(combined_stars)
    new_lead = (
        f"**{total_prs} merged {pluralize(total_prs, 'PR')} across "
        f"{project_count} {pluralize(project_count, 'project')}** "
        f"with a combined ⭐ {stars_text}"
    )

    new_block = LEAD_PATTERN.sub(lambda _: new_lead, block, count=1)
    if new_block == block:
        return

    new_readme = readme[:start] + new_block + readme[end:]
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)


if __name__ == "__main__":
    main()
