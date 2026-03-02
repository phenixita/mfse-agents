# MFSE Agents — AI Software Engineering Team

An evolving collection of AI agents that work together as a software engineering team. Each agent is a specialized prompt-driven persona — from requirements shaping to architecture, coding, and code review — designed to be composed into end-to-end development workflows.

The goal is to explore how AI agents can collaborate in structured pipelines, mimicking (and augmenting) the roles found in real software teams.

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
.claude-plugin/  — plugin manifest for distribution
```

## Contributing

1. Create or edit a folder under `agents/<agent-name>/`
2. Add/update the `<agent-name>.agent.md` file
3. Register the agent in `.claude-plugin/marketplace.json`
4. Update the agents table in this README

## License

[MIT](LICENSE) — Michele Ferracin
