#!/usr/bin/env python3
"""
iOS Interview-Prep Daily Digest
Reads prep_plan.json and writes today's lesson to an HTML file (GitHub Pages)
or prints it to stdout (dry-run / local testing).
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PLAN_PATH = Path(__file__).parent / "prep_plan.json"
DIFFICULTY_COLOR = {
    "Easy":   ("#16a34a", "#dcfce7"),
    "Medium": ("#d97706", "#fef3c7"),
    "Hard":   ("#e11d48", "#ffe4e6"),
}


def require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        sys.exit(f"[digest] ERROR: required environment variable '{name}' is not set.")
    return val


def weekday_count(start: date, end: date) -> int:
    """Number of weekdays (Mon-Fri) from start through end, inclusive."""
    if end < start:
        return 0
    days = (end - start).days + 1
    full_weeks, remainder = divmod(days, 7)
    count = full_weeks * 5
    sw = start.weekday()
    for i in range(remainder):
        if (sw + i) % 7 < 5:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Plain-text renderer (dry-run / logs)
# ---------------------------------------------------------------------------

def render_plain(plan: dict, idx: int, today: date, week_data: dict, day_data: dict) -> str:
    week_num = idx // 5 + 1
    day_num  = idx + 1
    weekday  = today.strftime("%A")

    lines = [
        f"Week {week_num}: {week_data['theme']}  |  {weekday}  |  Day {day_num} of 60",
        "=" * 60,
    ]

    if today.weekday() == 0:
        total_lc = sum(len(d["leetcode"]) for d in week_data["days"])
        lines += [
            "\nTHIS WEEK",
            f"  Theme:     {week_data['theme']}",
            f"  iOS Topic: {week_data['ios_topic']}",
            f"  LeetCode:  {total_lc} problems across 5 days",
            "",
        ]

    if day_data["leetcode"]:
        lines.append("LEETCODE")
        for p in day_data["leetcode"]:
            lines += [f"  [{p['difficulty']}] {p['name']}", f"    {p['url']}"]
        lines.append("")

    ios = day_data.get("ios")
    if ios:
        lines += ["IOS", f"  Topic: {ios['topic']}", f"  Task:  {ios['task']}"]
        if ios["type"] == "quiz" and ios.get("questions"):
            lines.append("  Questions:")
            for i, q in enumerate(ios["questions"], 1):
                lines.append(f"    {i}. {q}")
        elif ios["type"] == "system_design" and ios.get("prompt"):
            lines.append(f"  Prompt: {ios['prompt']}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

def badge(difficulty: str) -> str:
    fg, bg = DIFFICULTY_COLOR.get(difficulty, ("#374151", "#f3f4f6"))
    return (
        f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:700;'
        f'padding:2px 7px;border-radius:9999px;white-space:nowrap;">{difficulty}</span>'
    )


def render_html(plan: dict, idx: int, today: date, week_data: dict, day_data: dict) -> str:
    week_num = idx // 5 + 1
    day_num  = idx + 1
    weekday  = today.strftime("%A")
    title    = f"PrepPilot · Day {day_num} · Week {week_num}: {week_data['theme']}"

    sections = []

    if today.weekday() == 0:
        day_counts = "".join(
            f'<li style="margin:2px 0;"><strong>{d["day"]}</strong>: '
            f'{len(d["leetcode"])} problem{"s" if len(d["leetcode"]) != 1 else ""}</li>'
            for d in week_data["days"]
        )
        sections.append(f"""
<div style="background:#f0f9ff;border-left:4px solid #0284c7;padding:16px 20px;border-radius:6px;margin-bottom:24px;">
  <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:.05em;">This Week</p>
  <p style="margin:0 0 4px;font-size:15px;"><strong>Theme:</strong> {week_data['theme']}</p>
  <p style="margin:0 0 10px;font-size:15px;"><strong>iOS Topic:</strong> {week_data['ios_topic']}</p>
  <ul style="margin:0;padding-left:18px;font-size:14px;color:#374151;">{day_counts}</ul>
</div>""")

    if day_data["leetcode"]:
        rows = "".join(
            f'<tr>'
            f'<td style="padding:10px 12px 10px 0;border-bottom:1px solid #f3f4f6;">'
            f'<a href="{p["url"]}" style="color:#1d4ed8;text-decoration:none;font-weight:600;">{p["name"]}</a>'
            f'</td>'
            f'<td style="padding:10px 0 10px 12px;border-bottom:1px solid #f3f4f6;text-align:right;">'
            f'{badge(p["difficulty"])}'
            f'</td>'
            f'</tr>'
            for p in day_data["leetcode"]
        )
        sections.append(f"""
<h2 style="font-size:15px;font-weight:700;color:#111827;margin:0 0 10px;text-transform:uppercase;letter-spacing:.05em;">⚡ LeetCode</h2>
<table style="width:100%;border-collapse:collapse;font-size:14px;">{rows}</table>""")

    ios = day_data.get("ios")
    if ios:
        type_label = {"study": "📖 Study", "quiz": "🧠 Quiz", "system_design": "🏗 System Design"}.get(ios["type"], ios["type"])
        body = (
            f'<p style="margin:0 0 6px;font-size:14px;"><strong>Topic:</strong> {ios["topic"]}</p>'
            f'<p style="margin:0 0 12px;font-size:14px;">{ios["task"]}</p>'
        )
        if ios["type"] == "quiz" and ios.get("questions"):
            qs = "".join(
                f'<li style="margin-bottom:8px;font-size:14px;color:#1f2937;">{q}</li>'
                for q in ios["questions"]
            )
            body += f'<ol style="margin:0;padding-left:20px;">{qs}</ol>'
        elif ios["type"] == "system_design" and ios.get("prompt"):
            body += (
                f'<div style="background:#faf5ff;border-left:4px solid #7c3aed;padding:14px 18px;'
                f'border-radius:6px;font-size:14px;color:#4c1d95;font-style:italic;">'
                f'{ios["prompt"]}</div>'
            )
        sections.append(f"""
<h2 style="font-size:15px;font-weight:700;color:#111827;margin:24px 0 10px;text-transform:uppercase;letter-spacing:.05em;">{type_label}</h2>
{body}""")

    content = "\n".join(sections)
    updated = today.strftime("%B %-d, %Y")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <div style="max-width:600px;margin:32px auto;background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">
    <div style="background:#1e293b;padding:24px 28px;">
      <p style="margin:0 0 4px;font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;">Day {day_num} of 60</p>
      <h1 style="margin:0;font-size:22px;color:#f8fafc;font-weight:700;">Week {week_num}: {week_data['theme']}</h1>
      <p style="margin:6px 0 0;font-size:14px;color:#94a3b8;">{weekday} &middot; {today.strftime('%B %-d, %Y')}</p>
    </div>
    <div style="padding:28px;">{content}</div>
    <div style="padding:16px 28px;background:#f8fafc;border-top:1px solid #e5e7eb;text-align:center;">
      <p style="margin:0;font-size:12px;color:#9ca3af;">{plan['meta']['title']} &middot; Last updated {updated}</p>
    </div>
  </div>
</body>
</html>"""


def render_status_html(heading: str, message: str) -> str:
    """Simple page for weekend / not-started / complete states."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>PrepPilot</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <div style="max-width:600px;margin:80px auto;text-align:center;color:#374151;">
    <h1 style="font-size:24px;font-weight:700;color:#1e293b;">{heading}</h1>
    <p style="font-size:15px;">{message}</p>
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------

def _output_arg() -> str:
    """Return --output <path> value from argv, or empty string."""
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--output" and i < len(sys.argv):
            return sys.argv[i + 1]
        if arg.startswith("--output="):
            return arg.split("=", 1)[1]
    return ""


def deliver(html: str, plain: str, title: str, dry_run: bool, output_file: str) -> None:
    if dry_run:
        print("=" * 70)
        print(f"Title: {title}")
        print("=" * 70)
        print(plain)
        print("\n[HTML follows]\n")
        print(html)

    if output_file:
        out = Path(output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"[digest] Written → {out}")

    if not dry_run and not output_file:
        # Fallback: print to stdout so the run isn't silent
        print(html)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    dry_run     = "--dry-run" in sys.argv or os.environ.get("DRY_RUN", "").strip() not in ("", "0", "false", "False")
    output_file = _output_arg() or os.environ.get("OUTPUT_FILE", "").strip()

    start_str = require_env("START_DATE")
    try:
        start = date.fromisoformat(start_str)
    except ValueError:
        sys.exit(f"[digest] ERROR: START_DATE '{start_str}' is not a valid YYYY-MM-DD date.")

    today = date.today()

    if today.weekday() >= 5:
        print(f"[digest] Today ({today.strftime('%A')}) is a weekend — no digest.")
        if output_file:
            html = render_status_html("Rest Day 🛌", "It's the weekend — no prep today. See you Monday!")
            deliver(html, "", "Rest Day", dry_run=False, output_file=output_file)
        return

    if today < start:
        print(f"[digest] Plan starts {start} — today is {today}. No digest yet.")
        if output_file:
            html = render_status_html("Not started yet", f"The plan kicks off on {start.strftime('%B %-d, %Y')}.")
            deliver(html, "", "Not started", dry_run=False, output_file=output_file)
        return

    with open(PLAN_PATH, encoding="utf-8") as f:
        plan = json.load(f)

    idx = max(0, weekday_count(start, today) - 1)

    if idx > 59:
        body = (
            "You've finished all 60 lessons of the 12-week iOS interview-prep plan! "
            "Take stock of which patterns gave you trouble and spend the next week "
            "revisiting your weakest areas. Good luck with the interviews!"
        )
        html = render_status_html("Plan Complete 🎉", body)
        deliver(html, body, "Plan Complete", dry_run, output_file)
        return

    week_data = plan["weeks"][idx // 5]
    day_data  = week_data["days"][idx % 5]
    week_num  = idx // 5 + 1
    day_num   = idx + 1
    title     = f"Prep · Day {day_num} · Week {week_num}: {week_data['theme']}"

    plain = render_plain(plan, idx, today, week_data, day_data)
    html  = render_html(plan, idx, today, week_data, day_data)
    deliver(html, plain, title, dry_run, output_file)


if __name__ == "__main__":
    main()
