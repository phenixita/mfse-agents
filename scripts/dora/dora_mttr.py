#!/usr/bin/env python3
"""
DORA Metric 4 — Mean Time to Restore (MTTR).

Fetches closed Bug/Incident work items tagged 'production-incident' and computes
the average time from creation (incident start) to closure (service restored).

Usage:
    python dora_mttr.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN>
    python dora_mttr.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN> \\
        --from-date 2024-01-01 --to-date 2024-12-31 --incident-tag production-incident
"""

import argparse
import base64
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Missing dependency: install it with 'pip install requests'", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# DORA classification thresholds (MTTR in hours)
# ---------------------------------------------------------------------------
ELITE_THRESHOLD_H = 1.0      # < 1 hour
HIGH_THRESHOLD_H = 24.0      # < 1 day
MEDIUM_THRESHOLD_H = 24 * 7  # < 1 week


def classify(avg_hours: float) -> str:
    if avg_hours < ELITE_THRESHOLD_H:
        return "Elite"
    if avg_hours < HIGH_THRESHOLD_H:
        return "High"
    if avg_hours < MEDIUM_THRESHOLD_H:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def make_headers(pat: str) -> dict:
    token = base64.b64encode(f":{pat}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def get_json(url: str, headers: dict, params: dict = None) -> dict:
    response = requests.get(url, headers=headers, params=params)
    if not response.ok:
        print(f"HTTP {response.status_code} — {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def post_json(url: str, headers: dict, body: dict, params: dict = None) -> dict:
    response = requests.post(url, headers=headers, json=body, params=params)
    if not response.ok:
        print(f"HTTP {response.status_code} — {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


# ---------------------------------------------------------------------------
# Azure DevOps queries
# ---------------------------------------------------------------------------

def get_closed_incidents(
    base_url: str,
    org: str,
    headers: dict,
    from_dt: datetime,
    to_dt: datetime,
    incident_tag: str,
) -> list:
    """
    WIQL query for closed Bug/Incident items tagged production-incident,
    closed within the measurement window.
    """
    from_str = from_dt.strftime("%Y-%m-%d") if from_dt else "2000-01-01"
    to_str = to_dt.strftime("%Y-%m-%d") if to_dt else "2100-01-01"

    wiql = {
        "query": (
            f"SELECT [System.Id], [System.Title], [System.CreatedDate], "
            f"[Microsoft.VSTS.Common.ClosedDate], [System.WorkItemType] "
            f"FROM WorkItems "
            f"WHERE [System.WorkItemType] IN ('Bug', 'Incident') "
            f"AND [System.Tags] CONTAINS '{incident_tag}' "
            f"AND [System.State] = 'Closed' "
            f"AND [Microsoft.VSTS.Common.ClosedDate] >= '{from_str}' "
            f"AND [Microsoft.VSTS.Common.ClosedDate] <= '{to_str}' "
            f"ORDER BY [Microsoft.VSTS.Common.ClosedDate] ASC"
        )
    }

    url = f"{base_url}/_apis/wit/wiql"
    data = post_json(url, headers, wiql, params={"api-version": "7.1"})
    work_items = data.get("workItems", [])

    if not work_items:
        return []

    ids = [str(wi["id"]) for wi in work_items[:200]]
    details_url = f"{org.rstrip('/')}/_apis/wit/workItems"
    details = get_json(
        details_url,
        headers,
        params={
            "ids": ",".join(ids),
            "fields": "System.Id,System.CreatedDate,Microsoft.VSTS.Common.ClosedDate,System.WorkItemType",
            "api-version": "7.1",
        },
    )
    return details.get("value", [])


def parse_azdo_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    date_str = date_str[:26] + "Z" if len(date_str) > 27 else date_str
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def parse_date(value: str, end_of_day: bool = False) -> datetime:
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid date format '{value}'. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def compute_mttr(
    org: str,
    project: str,
    pat: str,
    from_date: str = None,
    to_date: str = None,
    incident_tag: str = "production-incident",
) -> dict:
    base_url = f"{org.rstrip('/')}/{project}"
    headers = make_headers(pat)

    from_dt = parse_date(from_date) if from_date else None
    to_dt = parse_date(to_date, end_of_day=True) if to_date else None

    print(f"Fetching closed production incidents (tag: '{incident_tag}')...", file=sys.stderr)
    incidents = get_closed_incidents(base_url, org, headers, from_dt, to_dt, incident_tag)
    print(f"  Closed incidents found: {len(incidents)}", file=sys.stderr)

    durations_h = []
    for item in incidents:
        fields = item.get("fields", {})
        created_dt = parse_azdo_date(fields.get("System.CreatedDate", ""))
        closed_dt = parse_azdo_date(fields.get("Microsoft.VSTS.Common.ClosedDate", ""))
        if created_dt and closed_dt and closed_dt >= created_dt:
            hours = (closed_dt - created_dt).total_seconds() / 3600
            durations_h.append(hours)

    if not durations_h:
        return {
            "metric": "mttr",
            "samples": 0,
            "avg_hours": None,
            "median_hours": None,
            "dora_level": "N/A",
            "incident_tag": incident_tag,
        }

    avg_hours = sum(durations_h) / len(durations_h)
    sorted_d = sorted(durations_h)
    n = len(sorted_d)
    median_hours = (
        sorted_d[n // 2]
        if n % 2 == 1
        else (sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2
    )
    level = classify(avg_hours)

    return {
        "metric": "mttr",
        "samples": len(durations_h),
        "avg_hours": round(avg_hours, 2),
        "median_hours": round(median_hours, 2),
        "dora_level": level,
        "incident_tag": incident_tag,
    }


def main():
    parser = argparse.ArgumentParser(
        description="DORA Metric 4 — Mean Time to Restore via Azure DevOps Work Items."
    )
    parser.add_argument("--org", required=True, help="Organization URL (e.g. https://dev.azure.com/myorg)")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--pat", required=True, help="Personal Access Token")
    parser.add_argument("--from-date", metavar="YYYY-MM-DD", help="Start of measurement window")
    parser.add_argument("--to-date", metavar="YYYY-MM-DD", help="End of measurement window")
    parser.add_argument(
        "--incident-tag",
        default="production-incident",
        help="Work item tag marking production incidents (default: production-incident)",
    )
    args = parser.parse_args()

    result = compute_mttr(
        org=args.org,
        project=args.project,
        pat=args.pat,
        from_date=args.from_date,
        to_date=args.to_date,
        incident_tag=args.incident_tag,
    )

    print(f"Mean Time to Restore (MTTR)")
    print(f"  Samples           : {result['samples']}")
    print(f"  Avg MTTR          : {result['avg_hours']} hours")
    print(f"  Median MTTR       : {result['median_hours']} hours")
    print(f"  DORA level        : {result['dora_level']}")


if __name__ == "__main__":
    main()
