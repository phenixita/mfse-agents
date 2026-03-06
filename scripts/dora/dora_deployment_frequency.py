#!/usr/bin/env python3
"""
DORA Metric 1 — Deployment Frequency.

Counts deployments to a named production environment over a time window and
classifies the team's performance level (Elite / High / Medium / Low).

Source of truth: Azure DevOps **Environments** (multi-stage YAML pipelines).
A "deployment" is an execution of a `deployment` job that targets an environment
whose name contains the configured keyword (default: "production").

Both succeeded and failed deployments are counted separately so that
dora_report.py can use the same deployment list for Change Failure Rate.
The DORA Deployment Frequency metric counts only SUCCEEDED deployments.

Usage:
    python dora_deployment_frequency.py \\
        --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN>
    python dora_deployment_frequency.py \\
        --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN> \\
        --from-date 2024-01-01 --to-date 2024-12-31 --env-keyword prod
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
# DORA classification thresholds (deployments per day)
# ---------------------------------------------------------------------------
ELITE_THRESHOLD = 1.0      # >= 1 deploy/day
HIGH_THRESHOLD = 1 / 7     # >= 1 deploy/week
MEDIUM_THRESHOLD = 1 / 30  # >= 1 deploy/month


def classify(deploys_per_day: float) -> str:
    if deploys_per_day >= ELITE_THRESHOLD:
        return "Elite"
    if deploys_per_day >= HIGH_THRESHOLD:
        return "High"
    if deploys_per_day >= MEDIUM_THRESHOLD:
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


# ---------------------------------------------------------------------------
# Azure DevOps — Environments API
# ---------------------------------------------------------------------------

def list_environments(base_url: str, headers: dict) -> list:
    """Return all environments defined in the project."""
    url = f"{base_url}/_apis/distributedtask/environments"
    data = get_json(url, headers, params={"api-version": "7.1", "top": 500})
    return data.get("value", [])


def get_environment_deployments(base_url: str, headers: dict, env_id: int) -> list:
    """
    Return all deployment records for a given environment.

    Records are returned newest-first. We fetch in pages of 100 and stop once
    all records in a page are older than the from_dt boundary (handled by the
    caller after this function returns the raw list).
    """
    url = f"{base_url}/_apis/distributedtask/environments/{env_id}/environmentdeploymentrecords"
    all_records = []
    top = 100

    # The endpoint does not support $skip; Azure DevOps returns a continuationToken
    # in the response body when there are more pages.
    continuation_token = None

    while True:
        params = {"api-version": "7.1", "top": top}
        if continuation_token:
            params["continuationToken"] = continuation_token

        data = get_json(url, headers, params=params)
        batch = data.get("value", [])
        all_records.extend(batch)

        continuation_token = data.get("continuationToken")
        if not continuation_token or not batch:
            break

    return all_records


def parse_azdo_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    # Azure DevOps timestamps have 7 fractional digits; Python supports up to 6
    date_str = date_str[:26] + "Z" if len(date_str) > 27 else date_str
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def collect_deployments(
    base_url: str,
    headers: dict,
    from_dt: datetime,
    to_dt: datetime,
    env_keyword: str,
) -> dict:
    """
    Return a dict with two lists:
      succeeded: list of finishTime datetimes for successful deployments
      all:       list of finishTime datetimes for all non-cancelled deployments
    """
    print("Fetching environments...", file=sys.stderr)
    environments = list_environments(base_url, headers)
    matched = [e for e in environments if env_keyword.lower() in e["name"].lower()]

    if not matched:
        print(
            f"  No environment found containing keyword '{env_keyword}'. "
            f"Available: {[e['name'] for e in environments]}",
            file=sys.stderr,
        )
        return {"succeeded": [], "all": []}

    print(f"  Matched environments: {[e['name'] for e in matched]}", file=sys.stderr)

    succeeded = []
    all_deployments = []

    for env in matched:
        env_name = env["name"]
        env_id = env["id"]
        print(f"  Fetching deployment records for '{env_name}'...", file=sys.stderr)

        records = get_environment_deployments(base_url, headers, env_id)
        print(f"    Raw records fetched: {len(records)}", file=sys.stderr)

        for record in records:
            result = record.get("result", "")
            finish_dt = parse_azdo_date(record.get("finishTime", ""))

            if not finish_dt:
                continue

            # Skip deployments outside the measurement window
            if from_dt and finish_dt < from_dt:
                continue
            if to_dt and finish_dt > to_dt:
                continue

            # Skip cancelled/skipped/abandoned — these are not attempts
            if result in ("canceled", "skipped", "abandoned"):
                continue

            all_deployments.append(finish_dt)
            if result == "succeeded":
                succeeded.append(finish_dt)

    return {"succeeded": succeeded, "all": all_deployments}


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
# Entry point (importable)
# ---------------------------------------------------------------------------

def compute_deployment_frequency(
    org: str,
    project: str,
    pat: str,
    from_date: str = None,
    to_date: str = None,
    env_keyword: str = "production",
) -> dict:
    base_url = f"{org.rstrip('/')}/{project}"
    headers = make_headers(pat)

    from_dt = parse_date(from_date) if from_date else None
    to_dt = parse_date(to_date, end_of_day=True) if to_date else None

    deployments = collect_deployments(base_url, headers, from_dt, to_dt, env_keyword)

    total_succeeded = len(deployments["succeeded"])
    total_attempted = len(deployments["all"])

    if from_dt and to_dt:
        days = max((to_dt - from_dt).total_seconds() / 86400, 1)
    else:
        days = 30  # default window when no dates provided

    per_day = total_succeeded / days
    per_week = per_day * 7
    level = classify(per_day)

    return {
        "metric": "deployment_frequency",
        "total_deployments": total_succeeded,
        "total_attempted": total_attempted,
        "period_days": round(days, 1),
        "per_day": round(per_day, 4),
        "per_week": round(per_week, 4),
        "dora_level": level,
        "env_keyword": env_keyword,
        # Pass the raw deployment list so dora_report.py can reuse it for CFR
        "_succeeded_datetimes": deployments["succeeded"],
        "_all_datetimes": deployments["all"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="DORA Metric 1 — Deployment Frequency via Azure DevOps Environments."
    )
    parser.add_argument("--org", required=True, help="Organization URL (e.g. https://dev.azure.com/myorg)")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--pat", required=True, help="Personal Access Token")
    parser.add_argument("--from-date", metavar="YYYY-MM-DD", help="Start of measurement window")
    parser.add_argument("--to-date", metavar="YYYY-MM-DD", help="End of measurement window")
    parser.add_argument(
        "--env-keyword",
        default="production",
        help="Keyword in environment name that identifies production (default: production)",
    )
    args = parser.parse_args()

    result = compute_deployment_frequency(
        org=args.org,
        project=args.project,
        pat=args.pat,
        from_date=args.from_date,
        to_date=args.to_date,
        env_keyword=args.env_keyword,
    )

    print(f"Deployment Frequency")
    print(f"  Succeeded deploys : {result['total_deployments']}")
    print(f"  Total attempted   : {result['total_attempted']}")
    print(f"  Period            : {result['period_days']} days")
    print(f"  Per day           : {result['per_day']}")
    print(f"  Per week          : {result['per_week']}")
    print(f"  DORA level        : {result['dora_level']}")


if __name__ == "__main__":
    main()
