# MFSE — Michele Ferracin Software Engineering Best Practices

A collection of best practices, tools, and resources for software engineering teams — from AI agents for Copilot and similar platforms, to scripts and Azure DevOps integrations for monitoring and improving software delivery performance.

The goal is to help teams move faster and deliver better software by combining AI-assisted workflows with concrete tooling: agents that act as specialized engineering personas (requirements shaping, architecture, coding, code review), and scripts that connect to Azure DevOps to track and improve team metrics.

## CoreSquad

`coreSquad` is the simplified, language-agnostic version of the extended squad.

It keeps the same role separation, but removes the extra discovery and escalation lanes from the default flow so agents can collaborate with less overhead and fewer premium requests. The emphasis is on one approved brief, explicit workflow gates, and asking the user for missing decisions before implementation begins.

### Core Pipeline (MFSE-CoreSquad-0x)

| Agent | Description |
| - | - |
| [mfse-coresquad-00-facilitator](agents/mfse-coresquad-00-facilitator.agent.md) | Turns a rough request into an approved implementation brief |
| [mfse-coresquad-01-orchestrator](agents/mfse-coresquad-01-orchestrator.agent.md) | Coordinates the flow through explicit intake, design, build, and review gates |
| [mfse-coresquad-02-architect](agents/mfse-coresquad-02-architect.agent.md) | Produces a lean design packet with files, contracts, invariants, and validation intent |
| [mfse-coresquad-05-dba-specialist](agents/mfse-coresquad-05-dba-specialist.agent.md) | Reviews persistence-sensitive changes for schema safety, migrations, queries, and rollout risk |
| [mfse-coresquad-03-coder](agents/mfse-coresquad-03-coder.agent.md) | Implements the approved plan with minimal scope and explicit verification |
| [mfse-coresquad-04-reviewer](agents/mfse-coresquad-04-reviewer.agent.md) | Reviews for blockers, regressions, contract drift, and validation gaps |

### Why CoreSquad

- Early clarification gate before architecture and coding
- Fewer handoffs and no mandatory premium escalation lane
- Optional DBA gate only when the task touches persistence, schema, or data rollout risk
- Leaner prompts that tell each role exactly when to stop and ask the user for help
- Clear agent-to-agent packet format to reduce miscommunication and rework

## Agents

### Pipeline (MFSE-ExtendedSquad-0x) — Requirements & Context

| Agent | Description |
| - | - |
| [mfse-extendedsquad-00-facilitator](agents/mfse-extendedsquad-00-facilitator.agent.md) | Shapes raw ideas into user stories and acceptance criteria |
| [mfse-extendedsquad-02-crawler](agents/mfse-extendedsquad-02-crawler.agent.md) | Fast codebase crawler for gathering context |
| [mfse-extendedsquad-01-crawler-azdo](agents/mfse-extendedsquad-01-crawler-azdo.agent.md) | Azure DevOps crawler for work items and wiki |
| [mfse-extendedsquad-03-azdo-wit](agents/mfse-extendedsquad-03-azdo-wit.agent.md) | Azure DevOps Boards work item management |

### Implementation Team (MFSE-ExtendedSquad-0x) — Design, Build, Review

| Agent | Description |
| - | - |
| [mfse-extendedsquad-04-orchestrator](agents/mfse-extendedsquad-04-orchestrator.agent.md) | Coordinates the implementation team through the workflow |
| [mfse-extendedsquad-05-architect](agents/mfse-extendedsquad-05-architect.agent.md) | Designs system blueprints, contracts, and boundaries |
| [mfse-extendedsquad-06-coder](agents/mfse-extendedsquad-06-coder.agent.md) | Implements blueprints following TDD or user-chosen approach |
| [mfse-extendedsquad-07-reviewer](agents/mfse-extendedsquad-07-reviewer.agent.md) | Audits code against blueprints and conventions |
| [mfse-extendedsquad-08-theopus](agents/mfse-extendedsquad-08-theopus.agent.md) | Escalation agent for genuinely hard problems |

### Skills

Reusable prompt modules that agents compose into their workflows.

| Skill | Used by | Description |
| - | - | - |
| [mfse-user-stories-writing](skills/mfse-user-stories-writing/SKILL.md) | Facilitator | BDD user story writing with Given/When/Then templates |
| [mfse-azure-devops-cli-boards](skills/mfse-azure-devops-cli-boards/SKILL.md) | Azdo WIT | Azure DevOps Boards CLI commands for work items |

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

1. **CoreSquad Facilitator** turns a rough idea into an approved implementation brief
2. **CoreSquad Orchestrator** checks context, creates the task branch, and manages the delivery gates
3. **CoreSquad Architect** produces a lean implementation packet
4. **CoreSquad DBA Specialist** joins only for persistence-sensitive work such as schema, migrations, or query risks
5. **CoreSquad Coder** implements the approved change and runs the required validation
6. **CoreSquad Reviewer** audits blockers, regressions, validation gaps, and persistence drift when relevant
7. **ExtendedSquad** remains available when you want dedicated discovery, Azure DevOps flows, or a heavier escalation structure

The extended squad follows a broader pipeline:

1. **Facilitator** turns a rough idea into crisp user stories with acceptance criteria
2. **Crawlers** gather codebase and project context needed for implementation
3. **Orchestrator** coordinates the implementation team
4. **Architect** produces a blueprint — contracts, boundaries, test scenarios
5. **Coder** implements the blueprint (TDD optional — user chooses the approach)
6. **Reviewer** audits the result against the blueprint and team conventions
7. **TheOpus** is called in when the team hits a genuinely hard or unusual problem

In both squads, the full implementation flow is typically initiated by the Facilitator and executed by the Orchestrator.

## Installing

```bash
copilot plugin install phenixita/mfse-swengineering
```

## Project Structure

```
agents/          — agent prompt files (<name>.agent.md)
skills/          — reusable prompt modules referenced by agents
scripts/         — standalone scripts for Azure DevOps monitoring and tooling
.claude-plugin/  — plugin manifest for distribution
```

## Contributing

1. Create or edit a file under `agents/`
2. Add/update the `<agent-name>.agent.md` file
3. Register the agent in `.claude-plugin/marketplace.json`
4. Update the agents table in this README

## License

[MIT](LICENSE) — Michele Ferracin
