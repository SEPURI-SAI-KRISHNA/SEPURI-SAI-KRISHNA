# `.github/scripts`

Automation scripts that keep the profile README accurate without manual edits.

## `update_oss_contributions.py`

**Purpose:** Refreshes only the lead summary line of the *Merged contributions* section inside the `<!-- OSS-CONTRIB:START … END -->` markers in `README.md`. It recomputes three numbers — total merged PR count, total project count, and combined star count — directly from the rows already in the table, then rewrites that single sentence in place.

**What it does:**
1. Reads `README.md` and extracts the block between the `OSS-CONTRIB` markers.
2. Parses each table row to identify the `owner/repo` slug and any inline PR-count annotation (e.g. `[4 merged PRs ↗]`).
3. Fetches the live `stargazers_count` for each project via the GitHub REST API (uses the `GITHUB_TOKEN` secret — no PAT required).
4. Formats and replaces the bold summary sentence, then writes the file back only if the text actually changed.

**What it never touches:**
- Individual table rows (project descriptions, PR links, star badge URLs).
- The "currently in review" `<details>` section.
- Any other part of `README.md`.

**Triggered by:** [`.github/workflows/oss-contributions.yml`](../workflows/oss-contributions.yml) — runs on the 1st of each month at 03:00 UTC and can be triggered manually from the Actions tab.
