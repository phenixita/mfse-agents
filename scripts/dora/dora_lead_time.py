#!/usr/bin/env python3
"""
DORA Metric 2 — Lead Time for Changes.

For each successful production deployment, fetches the associated commits and
computes the time from the earliest commit to the deployment finish.
Average across all deployments → Lead Time.

Production deployments are identified via Azure DevOps **Environments** (same
source as Metric 1): a deployment job targeting an environment whose name
contains the configured keyword (default: "production").

The commit list is fetched from the underlying pipeline build via:
  GET /_apis/build/builds/{build_id}/changes
where build_id comes from the environment deployment record's owner.id field.

Usage:
    python dora_lead_time.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN>
    python dora_lead_time.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN> \\
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
# DORA classification thresholds (lead time in hours)
# ---------------------------------------------------------------------------
ELITE_THRESHOLD_H = 1.0        # < 1 hour
HIGH_THRESHOLD_H = 24 * 7      # < 1 week
MEDIUM_THRESHOLD_H = 24 * 30   # < 1 month


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


def get_build_changes(base_url: str, headers: dict, build_id: int) -> list:
    url = f"{base_url}/_apis/build/builds/{build_id}/changes"
    data = get_json(url, headers, params={"api-version": "7.1"})
    return data.get("value", [])


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

def compute_lead_times(
    base_url: str,
    headers: dict,
    from_dt: datetime,
    to_dt: datetime,
    env_keyword: str,
) -> list:
    """Return list of lead time hours per successful production deployment."""
    print("Fetching environments...", file=sys.stderr)
    environments = list_environments(base_url, headers)
    matched = [e for e in environments if env_keyword.lower() in e["name"].lower()]

    if not matched:
        print(
            f"  No environment found containing keyword '{env_keyword}'. "
            f"Available: {[e['name'] for e in environments]}",
            file=sys.stderr,
        )
        return []

    print(f"  Matched environments: {[e['name'] for e in matched]}", file=sys.stderr)

    lead_times = []
    for env in matched:
        env_name = env["name"]
        print(f"  Fetching deployment records for '{env_name}'...", file=sys.stderr)
        records = get_environment_deployments(base_url, headers, env["id"])

        for record in records:
            if record.get("result") != "succeeded":
                continue

            finish_dt = parse_azdo_date(record.get("finishTime", ""))
            if not finish_dt:
                continue
            if from_dt and finish_dt < from_dt:
                continue
            if to_dt and finish_dt > to_dt:
                continue

            # owner.id is the pipeline build/run ID
            build_id = record.get("owner", {}).get("id")
            if not build_id:
                continue

            print(f"    Fetching changes for build #{build_id}...", file=sys.stderr)
            changes = get_build_changes(base_url, headers, build_id)
            if not changes:
                continue

            commit_dates = []
            for change in changes:
                # 'timestamp' holds the commit author date
                ts = parse_azdo_date(change.get("timestamp", ""))
                if ts:
                    commit_dates.append(ts)

            if not commit_dates:
                continue

            earliest_commit = min(commit_dates)
            delta_hours = (finish_dt - earliest_commit).total_seconds() / 3600
            if delta_hours >= 0:
                lead_times.append(delta_hours)

    return lead_times


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

def compute_lead_time(
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

    lead_times = compute_lead_times(base_url, headers, from_dt, to_dt, env_keyword)

    if not lead_times:
        return {
            "metric": "lead_time_for_changes",
            "samples": 0,
            "avg_hours": None,
            "median_hours": None,
            "dora_level": "N/A",
            "env_keyword": env_keyword,
        }

    avg_hours = sum(lead_times) / len(lead_times)
    sorted_times = sorted(lead_times)
    n = len(sorted_times)
    median_hours = (
        sorted_times[n // 2]
        if n % 2 == 1
        else (sorted_times[n // 2 - 1] + sorted_times[n // 2]) / 2
    )
    level = classify(avg_hours)

    return {
        "metric": "lead_time_for_changes",
        "samples": len(lead_times),
        "avg_hours": round(avg_hours, 2),
        "median_hours": round(median_hours, 2),
        "dora_level": level,
        "env_keyword": env_keyword,
    }


def main():
    parser = argparse.ArgumentParser(
        description="DORA Metric 2 — Lead Time for Changes via Azure Pipelines."
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

    result = compute_lead_time(
        org=args.org,
        project=args.project,
        pat=args.pat,
        from_date=args.from_date,
        to_date=args.to_date,
        env_keyword=args.env_keyword,
    )

    print(f"Lead Time for Changes")
    print(f"  Samples           : {result['samples']}")
    print(f"  Avg lead time     : {result['avg_hours']} hours")
    print(f"  Median lead time  : {result['median_hours']} hours")
    print(f"  DORA level        : {result['dora_level']}")


if __name__ == "__main__":
    main()
