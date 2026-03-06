#!/usr/bin/env python3
"""
DORA Report — Aggregated report of all 4 DORA metrics.

Calls each individual metric module and produces a unified report with:
- Raw values for each metric
- DORA performance level per metric (Elite / High / Medium / Low)
- Overall team DORA level (lowest of the four)
- Output as JSON or Markdown

Usage:
    python dora_report.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN>
    python dora_report.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN> \\
        --from-date 2024-01-01 --to-date 2024-12-31 --format markdown
"""

import argparse
import json
import sys
import os

# Allow imports from same directory
sys.path.insert(0, os.path.dirname(__file__))

from dora_deployment_frequency import compute_deployment_frequency
from dora_lead_time import compute_lead_time
from dora_change_failure_rate import compute_change_failure_rate
from dora_mttr import compute_mttr


# ---------------------------------------------------------------------------
# Overall level calculation
# ---------------------------------------------------------------------------

LEVEL_ORDER = ["Elite", "High", "Medium", "Low", "N/A"]


def overall_level(levels: list) -> str:
    """Return the worst (lowest) level among the provided levels."""
    valid = [l for l in levels if l != "N/A"]
    if not valid:
        return "N/A"
    return max(valid, key=lambda l: LEVEL_ORDER.index(l))


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

LEVEL_BADGE = {
    "Elite": "Elite",
    "High": "High",
    "Medium": "Medium",
    "Low": "Low",
    "N/A": "N/A",
}


def _fmt_hours(h) -> str:
    if h is None:
        return "N/A"
    if h < 1:
        return f"{h * 60:.1f} min"
    if h < 24:
        return f"{h:.1f} h"
    return f"{h / 24:.1f} days"


def to_markdown(report: dict) -> str:
    df = report["deployment_frequency"]
    lt = report["lead_time_for_changes"]
    cfr = report["change_failure_rate"]
    mttr = report["mttr"]
    overall = report["overall_dora_level"]
    meta = report["meta"]

    lines = [
        "# DORA Metrics Report",
        "",
        f"**Project:** {meta['project']}  ",
        f"**Period:** {meta['from_date'] or 'all time'} → {meta['to_date'] or 'today'}  ",
        f"**Overall DORA level:** **{overall}**",
        "",
        "---",
        "",
        "## 1. Deployment Frequency",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Total deployments | {df['total_deployments']} |",
        f"| Period | {df['period_days']} days |",
        f"| Per day | {df['per_day']} |",
        f"| Per week | {df['per_week']} |",
        f"| **DORA level** | **{df['dora_level']}** |",
        "",
        "## 2. Lead Time for Changes",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Samples | {lt['samples']} |",
        f"| Avg lead time | {_fmt_hours(lt['avg_hours'])} |",
        f"| Median lead time | {_fmt_hours(lt['median_hours'])} |",
        f"| **DORA level** | **{lt['dora_level']}** |",
        "",
        "## 3. Change Failure Rate",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Total deployments | {cfr['total_deployments']} |",
        f"| Linked incidents | {cfr['linked_incidents']} |",
        f"| CFR | {cfr['cfr_percent']}% |",
        f"| **DORA level** | **{cfr['dora_level']}** |",
        "",
        "## 4. Mean Time to Restore (MTTR)",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Samples | {mttr['samples']} |",
        f"| Avg MTTR | {_fmt_hours(mttr['avg_hours'])} |",
        f"| Median MTTR | {_fmt_hours(mttr['median_hours'])} |",
        f"| **DORA level** | **{mttr['dora_level']}** |",
        "",
        "---",
        "",
        "## DORA Level Reference",
        "",
        "| Metric | Elite | High | Medium | Low |",
        "| --- | --- | --- | --- | --- |",
        "| Deployment Frequency | Multiple/day | 1/day–1/week | 1/month | <1/month |",
        "| Lead Time | <1 hour | <1 week | <1 month | >1 month |",
        "| Change Failure Rate | 0–15% | 16–30% | >30% | >30% |",
        "| MTTR | <1 hour | <1 day | <1 week | >1 week |",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_report(
    org: str,
    project: str,
    pat: str,
    from_date: str = None,
    to_date: str = None,
    env_keyword: str = "production",
    incident_tag: str = "production-incident",
) -> dict:
    print("--- Deployment Frequency ---", file=sys.stderr)
    df = compute_deployment_frequency(org, project, pat, from_date, to_date, env_keyword)

    print("\n--- Lead Time for Changes ---", file=sys.stderr)
    lt = compute_lead_time(org, project, pat, from_date, to_date, env_keyword)

    print("\n--- Change Failure Rate ---", file=sys.stderr)
    cfr = compute_change_failure_rate(org, project, pat, from_date, to_date, env_keyword, incident_tag)

    print("\n--- MTTR ---", file=sys.stderr)
    mttr = compute_mttr(org, project, pat, from_date, to_date, incident_tag)

    levels = [df["dora_level"], lt["dora_level"], cfr["dora_level"], mttr["dora_level"]]

    return {
        "meta": {
            "org": org,
            "project": project,
            "from_date": from_date,
            "to_date": to_date,
            "env_keyword": env_keyword,
            "incident_tag": incident_tag,
        },
        "deployment_frequency": df,
        "lead_time_for_changes": lt,
        "change_failure_rate": cfr,
        "mttr": mttr,
        "overall_dora_level": overall_level(levels),
    }


def main():
    parser = argparse.ArgumentParser(
        description="DORA Report — aggregated report of all 4 DORA metrics."
    )
    parser.add_argument("--org", required=True, help="Organization URL (e.g. https://dev.azure.com/myorg)")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--pat", required=True, help="Personal Access Token")
    parser.add_argument("--from-date", metavar="YYYY-MM-DD", help="Start of measurement window")
    parser.add_argument("--to-date", metavar="YYYY-MM-DD", help="End of measurement window")
    parser.add_argument(
        "--env-keyword",
        default="production",
        help="Keyword in environment name identifying production (default: production)",
    )
    parser.add_argument(
        "--incident-tag",
        default="production-incident",
        help="Work item tag marking production incidents (default: production-incident)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format: json (default) or markdown",
    )
    args = parser.parse_args()

    report = build_report(
        org=args.org,
        project=args.project,
        pat=args.pat,
        from_date=args.from_date,
        to_date=args.to_date,
        env_keyword=args.env_keyword,
        incident_tag=args.incident_tag,
    )

    print("\n", file=sys.stderr)

    if args.format == "markdown":
        print(to_markdown(report))
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
