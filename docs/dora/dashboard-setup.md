# Azure DevOps Dashboard Setup — DORA Metrics

This guide explains how to configure Azure DevOps dashboards to visualize DORA metrics using native widgets and Analytics queries. No third-party tools required.

---

## Prerequisites

- Azure DevOps project with at least one active board or pipeline
- "Edit dashboard" permission (Project Administrator or team member with explicit grant)
- Analytics extension enabled (default in Azure DevOps Services; may need installation for Server)

---

## Dashboard creation

1. Navigate to **Boards > Overview > Dashboards**
2. Click **+ New Dashboard**
3. Name it `DORA Metrics` and choose team scope or project scope
4. Click **Edit** (pencil icon) to enter edit mode — now you can add widgets

---

## Widget 1 — Deployment Frequency (Pipeline History)

**Proxy:** Number of completed pipeline runs per period.

1. Click **+ Add Widget** → search for **Build History**
2. Configure:
   - **Build definition:** select your production pipeline
   - **Bar color:** choose a distinct color for production
3. For a count view, add a second **Chart for Work Items** widget with a flat count query (see WIQL below) or use the **Deployment Frequency** widget if available in your Azure DevOps tier.

**Alternative — Analytics widget:**
1. Add a **Burndown & Burnup** or **Velocity** widget (for sprint-based teams)
2. For release-based teams, use **Release Definition Overview** widget to show release cadence

---

## Widget 2 — Lead Time for Changes (Cycle Time)

**Native widget:** Cycle Time (requires Azure Boards)

1. Click **+ Add Widget** → search for **Cycle Time**
2. Configure:
   - **Teams:** select your team
   - **Work item types:** User Story / Feature
   - **Time period:** last 30 or 90 days
3. The widget shows the rolling average from "Active" to "Closed" — a proxy for lead time when combined with PR and pipeline data.

**Note:** True lead time (commit → production) requires OData queries or the Python scripts in `scripts/dora/`.

---

## Widget 3 — Change Failure Rate (Bug Count)

**Proxy:** Count of production incidents (Bugs with `production-incident` tag) per sprint or month.

1. Click **+ Add Widget** → search for **Chart for Work Items**
2. Click the widget settings gear → **Configure**
3. Create or select a query:
   ```
   SELECT [System.Id], [System.Title]
   FROM WorkItems
   WHERE [System.WorkItemType] = 'Bug'
   AND [System.Tags] CONTAINS 'production-incident'
   AND [System.CreatedDate] >= @StartOfMonth
   ```
4. Set chart type to **Column** grouped by **Month**
5. Overlay with a line showing total deploys for the same period (manual or via second widget)

---

## Widget 4 — MTTR (Work Item Age for Critical Bugs)

**Native widget:** Lead Time (shows time from activation to closure)

1. Click **+ Add Widget** → search for **Lead Time**
2. Configure:
   - **Work item types:** Bug
   - Filter by tag: `production-incident` (requires a saved query)
   - **Time period:** last 90 days
3. The P50/P85 lines in the chart represent your median and P85 MTTR respectively.

**Alternative — Chart for Work Items:**
1. Use the query below and chart by **Closed Date** grouped by week:
   ```
   SELECT [System.Id], [Microsoft.VSTS.Common.ClosedDate], [System.CreatedDate]
   FROM WorkItems
   WHERE [System.WorkItemType] = 'Bug'
   AND [System.Tags] CONTAINS 'production-incident'
   AND [System.State] = 'Closed'
   ```

---

## OData / Analytics queries (advanced)

For teams on Azure DevOps Services, use the **Embedded Iframe** widget to display Power BI reports backed by Analytics OData.

### Deployment frequency (OData)
```
https://analytics.dev.azure.com/{org}/{project}/_odata/v3.0-preview/PipelineRuns
  ?$filter=PipelineRunCompletedOn/Date ge 2024-01-01
    and CompletedStageName eq 'production'
    and ResultName eq 'succeeded'
  &$apply=groupby((PipelineRunCompletedOn/Year,PipelineRunCompletedOn/Month),aggregate($count as RunCount))
```

### MTTR (OData)
```
https://analytics.dev.azure.com/{org}/{project}/_odata/v3.0-preview/WorkItems
  ?$filter=WorkItemType eq 'Bug'
    and TagNames/any(t: t eq 'production-incident')
    and StateCategory eq 'Completed'
  &$select=WorkItemId,CreatedDate,ClosedDate,LeadTimeDays
```

---

## Kanban teams (no pipelines)

Teams using Kanban without formal pipelines (e.g., Starch) can still track proxy metrics:

| DORA Metric | Kanban Proxy | Widget |
| --- | --- | --- |
| Deployment Frequency | Stories/Features moved to "Done" per week | Velocity or Throughput |
| Lead Time | Cycle time from "Active" to "Done" | Cycle Time widget |
| Change Failure Rate | Bugs created after a story is closed | Chart for Work Items |
| MTTR | Age of bugs from creation to closure | Lead Time widget (Bugs only) |

**Recommended dashboard layout for Kanban teams:**
1. Throughput chart (items completed per week)
2. Cycle Time scatter plot (last 90 days)
3. Bug count by sprint (production-incident tag)
4. Lead time chart (bugs only)

---

## Refreshing data

- Widget data refreshes every **30 minutes** by default
- For manual refresh: open the dashboard and click the **Refresh** icon (top right)
- Analytics queries have up to **30 minutes** latency after work item or build changes

---

## Next steps

- See `collection-guide.md` for the prerequisite tagging and pipeline setup
- Use `scripts/dora/dora_report.py` for precise metric computation outside the dashboard
