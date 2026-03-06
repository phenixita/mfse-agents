# MFSE — Software Engineering Best Practices

A collection of best practices, tools, and resources for software engineering teams — from AI agents for Copilot and similar platforms, to scripts and Azure DevOps integrations for monitoring and improving software delivery performance.

The goal is to help teams move faster and deliver better software by combining AI-assisted workflows with concrete tooling: agents that act as specialized engineering personas (requirements shaping, architecture, coding, code review), and scripts that connect to Azure DevOps to track and improve team metrics.

## Agents

### Pipeline (MFSE-0x) — Requirements & Context

| Agent | Description |
| - | - |
| [mfse-00-facilitator](agents/mfse-00-facilitator/mfse-00-facilitator.agent.md) | Shapes raw ideas into user stories and acceptance criteria |
| [mfse-01-crawler](agents/mfse-01-crawler/mfse-01-crawler.agent.md) | Fast codebase crawler for gathering context |
| [mfse-01-crawler-azdo](agents/mfse-01-crawler-azdo/mfse-01-crawler-azdo.agent.md) | Azure DevOps crawler for work items and wiki |
| [mfse-02-azdo-wit](agents/mfse-02-azdo-wit/mfse-02-azdo-wit.agent.md) | Azure DevOps Boards work item management |

### Implementation Team (MFSE-1x) — Design, Build, Review

| Agent | Description |
| - | - |
| [mfse-10-orchestrator](agents/mfse-10-orchestrator/mfse-10-orchestrator.agent.md) | Coordinates the implementation team through the workflow |
| [mfse-11-architect](agents/mfse-11-architect/mfse-11-architect.agent.md) | Designs system blueprints, contracts, and boundaries |
| [mfse-12-coder](agents/mfse-12-coder/mfse-12-coder.agent.md) | Implements blueprints following TDD or user-chosen approach |
| [mfse-13-reviewer](agents/mfse-13-reviewer/mfse-13-reviewer.agent.md) | Audits code against blueprints and conventions |
| [mfse-14-theopus](agents/mfse-14-theopus/mfse-14-theopus.agent.md) | Escalation agent for genuinely hard problems |

### End-to-End

| Agent | Description |
| - | - |
| [mfse-e2e](agents/mfse-e2e/mfse-e2e.agent.md) | Full pipeline: idea to user story to architecture to code to review |

### Skills

Reusable prompt modules that agents compose into their workflows.

| Skill | Used by | Description |
| - | - | - |
| [mfse-user-stories-writing](skills/mfse-user-stories-writing/SKILL.md) | Facilitator | BDD user story writing with Given/When/Then templates |
| [mfse-azure-devops-cli-boards](skills/mfse-azure-devops-cli-boards/SKILL.md) | Azdo WIT | Azure DevOps Boards CLI commands for work items |

## DORA Metrics Toolkit

A complete toolkit for measuring and improving software delivery performance using the 4 DORA metrics — Deployment Frequency, Lead Time for Changes, Change Failure Rate, and Mean Time to Restore.

### The 4 metrics

| Metric | What it measures | DORA Elite benchmark |
| - | - | - |
| Deployment Frequency | How often code reaches production | Multiple deploys/day |
| Lead Time for Changes | Time from first commit to production | < 1 hour |
| Change Failure Rate | % of deploys that cause incidents | 0–15% |
| MTTR | Time to restore after a failure | < 1 hour |

### Scripts

| Script | Metric | Description |
| - | - | - |
| [dora_deployment_frequency.py](scripts/dora/dora_deployment_frequency.py) | Metric 1 | Count production deployments per day/week and classify Elite/High/Medium/Low |
| [dora_lead_time.py](scripts/dora/dora_lead_time.py) | Metric 2 | Average time from first commit to production deployment |
| [dora_change_failure_rate.py](scripts/dora/dora_change_failure_rate.py) | Metric 3 | % of deployments that triggered a production incident within 24h |
| [dora_mttr.py](scripts/dora/dora_mttr.py) | Metric 4 | Average time to close production incidents |
| [dora_report.py](scripts/dora/dora_report.py) | All | Unified report — JSON or Markdown — with overall DORA level |

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Full DORA report (JSON)
python scripts/dora/dora_report.py \
  --org https://dev.azure.com/myorg \
  --project MyProject \
  --pat <TOKEN> \
  --from-date 2024-01-01 \
  --to-date 2024-12-31

# Full DORA report (Markdown)
python scripts/dora/dora_report.py \
  --org https://dev.azure.com/myorg \
  --project MyProject \
  --pat <TOKEN> \
  --from-date 2024-01-01 \
  --to-date 2024-12-31 \
  --format markdown

# Individual metric
python scripts/dora/dora_deployment_frequency.py \
  --org https://dev.azure.com/myorg \
  --project MyProject \
  --pat <TOKEN> \
  --prod-keyword production
```

### Guides

- [Dashboard Setup](docs/dora/dashboard-setup.md) — configure Azure DevOps native widgets for DORA visualization
- [Collection Guide](docs/dora/collection-guide.md) — prerequisite setup for pipelines, tags, and branch policies (start here with a new team)

### Agent

| Agent | Description |
| - | - |
| [mfse-20-dora-analyst](agents/mfse-20-dora-analyst.agent.md) | On-demand DORA analysis via Azure DevOps MCP — natural language queries, benchmarking, recommendations |

---

## Scripts & Azure DevOps Integrations

Standalone scripts to monitor team performance and support continuous improvement of software delivery.

| Script | Description |
| - | - |
| [azdo_closed_prs.py](scripts/azdo_closed_prs.py) | Count completed (merged) pull requests across all repositories in an Azure DevOps project, with optional date range filtering |

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Run
python scripts/azdo_closed_prs.py \
  --org https://dev.azure.com/myorg \
  --project MyProject \
  --pat <TOKEN> \
  --from-date 2024-01-01 \
  --to-date 2024-12-31
```

## How It Works

The agents follow a structured pipeline that mirrors a real engineering team:

1. **Facilitator** turns a rough idea into crisp user stories with acceptance criteria
2. **Crawlers** gather codebase and project context needed for implementation
3. **Orchestrator** coordinates the implementation team
4. **Architect** produces a blueprint — contracts, boundaries, test scenarios
5. **Coder** implements the blueprint (TDD optional — user chooses the approach)
6. **Reviewer** audits the result against the blueprint and team conventions
7. **TheOpus** is called in when the team hits a genuinely hard or unusual problem

The **mfse-e2e** agent chains the full pipeline into a single invocation.

## Installing

```bash
copilot plugin install phenixita/mfse-swengineering
```

## Project Structure

```
agents/          — one folder per agent, each with a <name>.agent.md prompt
skills/          — reusable prompt modules referenced by agents
scripts/         — standalone scripts for Azure DevOps monitoring and tooling
.claude-plugin/  — plugin manifest for distribution
```

## Contributing

1. Create or edit a folder under `agents/<agent-name>/`
2. Add/update the `<agent-name>.agent.md` file
3. Register the agent in `.claude-plugin/marketplace.json`
4. Update the agents table in this README

## License

[MIT](LICENSE) — Michele Ferracin
