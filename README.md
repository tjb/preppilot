# iOS Interview-Prep Digest

A GitHub Action that publishes a daily interview-prep digest to **GitHub Pages** based on `prep_plan.json` — a 12-week iOS senior/staff interview plan covering LeetCode patterns and iOS deep-dives.

Visit your Pages URL each morning to see today's lesson.

## What it does

Each weekday the workflow runs `digest.py`, which:

1. Reads `START_DATE` (the day you began the plan).
2. Counts weekdays (Monday–Friday) from `START_DATE` through today. That count − 1 is the lesson index (0–59).
3. Maps the index to the correct week and day in `prep_plan.json` (`weeks[idx // 5].days[idx % 5]`).
4. Renders an HTML page and deploys it to GitHub Pages.

**Weekday-only logic:** The workflow only runs Mon–Fri. If triggered manually on a weekend it writes a "Rest Day" placeholder so the site still loads. Before `START_DATE` it shows a "not started yet" page. After all 60 lessons it shows a "plan complete" page.

**Monday bonus:** On Mondays the page prepends a "This Week" overview card with the week's theme, iOS topic, and per-day problem counts.

## Setup

### 1. Enable GitHub Pages

In your repo go to **Settings → Pages** and set:
- **Source:** GitHub Actions

That's it — the workflow handles the rest.

### 2. Repo variable — `START_DATE`

In **Settings → Secrets and variables → Actions → Variables** add:

| Name | Value (example) |
|------|----------------|
| `START_DATE` | `2026-06-16` |

Set this to the Monday you started (or plan to start) the 12-week program.

### 3. No secrets needed

GitHub Pages deployment uses the built-in `GITHUB_TOKEN` — no SMTP credentials or third-party accounts required.

## Schedule

The workflow runs at **13:30 UTC every weekday** (`30 13 * * 1-5`).

> **Note:** GitHub Actions cron is always UTC and does not adjust for Daylight Saving Time.
> 13:30 UTC ≈ 8:30 AM Central in summer (CDT, UTC−5) and 7:30 AM Central in winter (CST, UTC−6).
> Edit the `cron:` line in `.github/workflows/digest.yml` to match your preferred local time.

## Testing

### Manual workflow run (dry run)

In your repo go to **Actions → Daily Prep Digest → Run workflow**.  
Leave "dry_run" checked (default `true`). The digest HTML will print to the job logs but **won't overwrite your live Pages site**.

### Local dry run

```bash
DRY_RUN=1 START_DATE=2026-06-16 python digest.py
```

Test a specific day by adjusting `START_DATE`:

```bash
# Simulate Day 4 (Thursday quiz) — set START_DATE 3 weekdays before today
DRY_RUN=1 START_DATE=2026-06-09 python digest.py

# Write to a local file instead
OUTPUT_FILE=/tmp/digest.html START_DATE=2026-06-16 python digest.py
open /tmp/digest.html   # preview in browser
```

No dependencies beyond the Python standard library — no `pip install` needed.
