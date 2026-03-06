# Azure DevOps Data Collection Guide — DORA Metrics

This guide describes the prerequisites that a team must configure in Azure DevOps **before** DORA metrics can be collected reliably. Follow this checklist at the start of a consultancy engagement or when onboarding a new team.

---

## Why this matters

DORA metrics are only as accurate as the underlying data. If pipelines are not tagged for production, if bugs are not consistently classified, or if there is no branch policy enforcing PRs, the scripts and dashboards will return misleading results or no data at all.

---

## Step 1 — Name production pipelines consistently

**Required for:** Deployment Frequency, Lead Time, Change Failure Rate

Every pipeline (or stage within a multi-stage pipeline) that deploys to production must have a recognizable keyword in its name.

**Action:**
1. Go to **Pipelines > All Pipelines**
2. Rename any pipeline that deploys to production to include the word `production` or `prod` in the definition name. Example: `api-service-production`, `web-deploy-prod`
3. If using multi-stage YAML pipelines, ensure the production stage is named `production` or `prod`:
   ```yaml
   stages:
     - stage: production
       displayName: Deploy to Production
       jobs:
         - deployment: deploy
           environment: production
   ```
4. If using Release pipelines, name the production environment `production` or `prod`.

**Verify:** Run `dora_deployment_frequency.py` — it should list at least one build.

---

## Step 2 — Tag production incidents

**Required for:** Change Failure Rate, MTTR

Every Bug or Incident work item that represents a production failure must be tagged with `production-incident`.

**Action:**
1. Go to **Boards > Work Items**
2. Create a saved query for all Bugs in state "Active" to review existing items
3. Add the tag `production-incident` to any bug that:
   - Was discovered in production
   - Caused service disruption or degradation
   - Required a hotfix or rollback
4. For new incidents, establish a team agreement: the person opening the bug tags it `production-incident` before saving.

**Optional — use Severity field:**
- Set Severity = 1 (Critical) or 2 (High) for production incidents
- This allows additional filtering in the scripts and dashboards

**Verify:** Open **Boards > Queries**, create a flat query with:
```
Work Item Type = Bug
Tags contains production-incident
```
If the list is empty and you have had incidents, tag them now.

---

## Step 3 — Enable branch policies for main/master

**Required for:** Lead Time for Changes (enables PR-based tracking)

Without branch policies, developers can push directly to main, bypassing the commit-to-PR-to-deploy flow that DORA Lead Time assumes.

**Action:**
1. Go to **Project Settings > Repositories > [your repo] > Policies**
2. Under **Branch Policies**, select the `main` (or `master`) branch
3. Enable:
   - **Require a minimum number of reviewers** (minimum 1)
   - **Check for linked work items** (optional, but improves traceability)
   - **Require comment resolution** (optional)
4. Click **Save**

**Result:** All changes to main now go through a PR, which creates a clear audit trail for Lead Time calculation.

---

## Step 4 — Link work items to PRs and builds

**Required for:** accurate Lead Time and CFR traceability

**Action for PRs:**
1. When creating a PR, always link the related User Story or Bug in the **Work Items** field
2. This can be enforced via the "Require linked work items" branch policy (Step 3)

**Action for builds:**
1. In YAML pipelines, the build system automatically captures commits. No extra action needed.
2. For classic build pipelines, ensure the source repository is correctly configured — the `/_apis/build/builds/{id}/changes` API will return commits automatically.

---

## Step 5 — Define and document your deployment environment

**Required for:** unambiguous Deployment Frequency measurement

Agree on a clear definition of "production deployment" with the team:

| Question | Answer to document |
| --- | --- |
| What counts as a deploy? | Pipeline run completing the `production` stage |
| What counts as a failure? | Bug tagged `production-incident` within 24h of deploy |
| What counts as restored? | The incident Bug/Incident moved to `Closed` state |
| Who closes incidents? | On-call engineer or team lead |

Document this in your team wiki or in a work item pinned to the top of the backlog.

---

## Onboarding checklist (Day 1 with a new team)

Use this checklist during the first consultancy session:

- [ ] **Pipeline audit**: list all pipelines → identify which ones deploy to production → rename with `production`/`prod` keyword
- [ ] **Incident audit**: review last 3 months of Bugs → tag production incidents retroactively
- [ ] **Branch policy**: enable PR requirement on `main`/`master` in all active repos
- [ ] **Work item linking**: confirm team agreement to link bugs and stories to PRs
- [ ] **Team agreement**: document the definitions above in the project wiki
- [ ] **Baseline run**: run `dora_report.py` against historical data to establish the starting baseline

---

## Minimum viable setup (MVP — for small teams or new projects)

If the team has very limited history and no CI/CD yet, focus on:

1. Tag future production incidents as `production-incident` (enables CFR + MTTR immediately)
2. Name any future production pipeline with the keyword `production` (enables Deployment Frequency)
3. Enable branch policies (enables Lead Time tracking going forward)

After 30 days with this setup, run `dora_report.py` for the first data-driven baseline.

---

## Related resources

- `docs/dora/dashboard-setup.md` — how to configure Azure DevOps dashboards for these metrics
- `scripts/dora/dora_report.py` — automated report generation via CLI
- [DORA State of DevOps Report](https://dora.dev) — official benchmarks and research
