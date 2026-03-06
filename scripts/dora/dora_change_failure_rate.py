#!/usr/bin/env python3
"""
DORA Metric 3 — Change Failure Rate.

Counts production deployments (succeeded + failed, via Azure DevOps Environments)
in the window, then counts Bug/Incident work items tagged 'production-incident'
created within 24 hours of each deployment.
CFR = incident_count / total_deployment_attempts.

Production deployments are identified via Azure DevOps **Environments** (same
source as Metric 1): deployment jobs targeting an environment whose name contains
the configured keyword (default: "production").

Usage:
    python dora_change_failure_rate.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN>
    python dora_change_failure_rate.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN> \\
        --from-date 2024-01-01 --to-date 2024-12-31 --env-keyword prod --incident-tag production-incident
"""

import argparse
import base64
import json
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("Missing dependency: install it with 'pip install requests'", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# DORA classification thresholds (CFR as a fraction, 0–1)
# ---------------------------------------------------------------------------

def classify(cfr: float) -> str:
    if cfr <= 0.15:
        return "Elite"
    if cfr <= 0.30:
        return "High"
    return "Low"  # Medium/Low share the >30% bucket per DORA 2023


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

def list_environments(base_url: str, headers: dict) -> list:
    url = f"{base_url}/_apis/distributedtask/environments"
    data = get_json(url, headers, params={"api-version": "7.1", "top": 500})
    return data.get("value", [])


def get_environment_deployments(base_url: str, headers: dict, env_id: int) -> list:
    url = f"{base_url}/_apis/distributedtask/environments/{env_id}/environmentdeploymentrecords"
    all_records = []
    continuation_token = None
    while True:
        params = {"api-version": "7.1", "top": 100}
        if continuation_token:
            params["continuationToken"] = continuation_token
        data = get_json(url, headers, params=params)
        batch = data.get("value", [])
        all_records.extend(batch)
        continuation_token = data.get("continuationToken")
        if not continuation_token or not batch:
            break
    return all_records


def get_production_incidents(
    base_url: str,
    org: str,
    headers: dict,
    from_dt: datetime,
    to_dt: datetime,
    incident_tag: str,
) -> list:
    """
    Run a WIQL query to fetch Bug/Incident work items tagged with `incident_tag`
    created in the measurement window.
    """
    # Extend window slightly to catch incidents created up to 24h after last deploy
    window_end = to_dt + timedelta(hours=24) if to_dt else None
    from_str = from_dt.strftime("%Y-%m-%d") if from_dt else "2000-01-01"
    to_str = window_end.strftime("%Y-%m-%d") if window_end else "2100-01-01"

    wiql = {
        "query": (
            f"SELECT [System.Id], [System.Title], [System.CreatedDate], [System.WorkItemType] "
            f"FROM WorkItems "
            f"WHERE [System.WorkItemType] IN ('Bug', 'Incident') "
            f"AND [System.Tags] CONTAINS '{incident_tag}' "
            f"AND [System.CreatedDate] >= '{from_str}' "
            f"AND [System.CreatedDate] <= '{to_str}' "
            f"ORDER BY [System.CreatedDate] ASC"
        )
    }

    url = f"{base_url}/_apis/wit/wiql"
    data = post_json(url, headers, wiql, params={"api-version": "7.1"})
    work_items = data.get("workItems", [])

    if not work_items:
        return []

    # Fetch details in batch (max 200 per request)
    ids = [str(wi["id"]) for wi in work_items[:200]]
    details_url = f"{org.rstrip('/')}/_apis/wit/workItems"
    details = get_json(
        details_url,
        headers,
        params={
            "ids": ",".join(ids),
            "fields": "System.Id,System.CreatedDate,System.WorkItemType",
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

def count_failures(deployments: list, incidents: list) -> int:
    """
    Count incidents created within 24 hours after any deployment.
    A deployment is a datetime. An incident is a work item dict with CreatedDate.
    """
    failures = 0
    counted_incidents = set()

    for deploy_dt in deployments:
        window_end = deploy_dt + timedelta(hours=24)
        for incident in incidents:
            inc_id = incident.get("id")
            if inc_id in counted_incidents:
                continue
            created_str = incident.get("fields", {}).get("System.CreatedDate", "")
            created_dt = parse_azdo_date(created_str)
            if created_dt and deploy_dt <= created_dt <= window_end:
                failures += 1
                counted_incidents.add(inc_id)

    return failures


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

def compute_change_failure_rate(
    org: str,
    project: str,
    pat: str,
    from_date: str = None,
    to_date: str = None,
    env_keyword: str = "production",
    incident_tag: str = "production-incident",
) -> dict:
    base_url = f"{org.rstrip('/')}/{project}"
    headers = make_headers(pat)

    from_dt = parse_date(from_date) if from_date else None
    to_dt = parse_date(to_date, end_of_day=True) if to_date else None

    # --- deployments: all non-cancelled attempts to production environment ---
    print("Fetching environments...", file=sys.stderr)
    environments = list_environments(base_url, headers)
    matched = [e for e in environments if env_keyword.lower() in e["name"].lower()]
    print(f"  Matched environments: {[e['name'] for e in matched]}", file=sys.stderr)

    deployments = []
    for env in matched:
        records = get_environment_deployments(base_url, headers, env["id"])
        for record in records:
            if record.get("result") in ("canceled", "skipped", "abandoned"):
                continue
            dt = parse_azdo_date(record.get("finishTime", ""))
            if not dt:
                continue
            if from_dt and dt < from_dt:
                continue
            if to_dt and dt > to_dt:
                continue
            deployments.append(dt)

    print(f"  Total deployment attempts: {len(deployments)}", file=sys.stderr)

    print(f"Fetching production incidents (tag: '{incident_tag}')...", file=sys.stderr)
    incidents = get_production_incidents(base_url, org, headers, from_dt, to_dt, incident_tag)
    print(f"  Production incidents: {len(incidents)}", file=sys.stderr)

    if not deployments:
        return {
            "metric": "change_failure_rate",
            "total_deployments": 0,
            "linked_incidents": 0,
            "cfr_percent": None,
            "dora_level": "N/A",
            "env_keyword": env_keyword,
            "incident_tag": incident_tag,
        }

    failures = count_failures(deployments, incidents)
    cfr = failures / len(deployments)
    level = classify(cfr)

    return {
        "metric": "change_failure_rate",
        "total_deployments": len(deployments),
        "linked_incidents": failures,
        "cfr_percent": round(cfr * 100, 2),
        "dora_level": level,
        "env_keyword": env_keyword,
        "incident_tag": incident_tag,
    }


def main():
    parser = argparse.ArgumentParser(
        description="DORA Metric 3 — Change Failure Rate via Azure Pipelines + Work Items."
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
        help="Work item tag that marks production incidents (default: production-incident)",
    )
    args = parser.parse_args()

    result = compute_change_failure_rate(
        org=args.org,
        project=args.project,
        pat=args.pat,
        from_date=args.from_date,
        to_date=args.to_date,
        env_keyword=args.env_keyword,
        incident_tag=args.incident_tag,
    )

    print(f"Change Failure Rate")
    print(f"  Total deployments : {result['total_deployments']}")
    print(f"  Linked incidents  : {result['linked_incidents']}")
    print(f"  CFR               : {result['cfr_percent']}%")
    print(f"  DORA level        : {result['dora_level']}")


if __name__ == "__main__":
    main()
