# MFSE Agent Team

A multi-agent development team for coding agents. Orchestrates requirement shaping, architecture, implementation, and code review through specialized agents.

## Available Agents

### Pipeline Agents (MFSE-0x)

| Agent | Description |
| - | - |
| [mfse-00-facilitator](agents/mfse-00-facilitator/mfse-00-facilitator.agent.md) | Shapes requirements into user stories and acceptance criteria |
| [mfse-01-crawler](agents/mfse-01-crawler/mfse-01-crawler.agent.md) | Fast codebase crawler for gathering context |
| [mfse-01-crawler-azdo](agents/mfse-01-crawler-azdo/mfse-01-crawler-azdo.agent.md) | Azure DevOps crawler for work items and wiki |
| [mfse-02-azdo-wit](agents/mfse-02-azdo-wit/mfse-02-azdo-wit.agent.md) | Azure DevOps Boards work item management |

### Implementation Team (MFSE-1x)

| Agent | Description |
| - | - |
| [mfse-10-orchestrator](agents/mfse-10-orchestrator/mfse-10-orchestrator.agent.md) | Workflow orchestrator coordinating the team |
| [mfse-11-architect](agents/mfse-11-architect/mfse-11-architect.agent.md) | Lead Architect for system design and blueprints |
| [mfse-12-coder](agents/mfse-12-coder/mfse-12-coder.agent.md) | Expert Developer implementing blueprints |
| [mfse-13-reviewer](agents/mfse-13-reviewer/mfse-13-reviewer.agent.md) | Strict code reviewer and quality gate |
| [mfse-14-theopus](agents/mfse-14-theopus/mfse-14-theopus.agent.md) | Ultimate problem solver for hard issues |

### End-to-End

| Agent | Description |
| - | - |
| [mfse-e2e](agents/mfse-e2e/mfse-e2e.agent.md) | Full pipeline: idea → user story → architecture → code → review |

### Supporting Skills

Skills are lightweight prompts that agents reference for specialized tasks.

| Skill | Used by | Description |
| - | - |
| [mfse-user-stories-writing](skills/mfse-user-stories-writing/SKILL.md) | Facilitator | BDD user story writing with Given/When/Then templates |
| [mfse-azure-devops-cli-boards](skills/mfse-azure-devops-cli-boards/SKILL.md) | Azdo WIT | Azure DevOps Boards CLI commands for work items |

## How It Works

The team follows a structured pipeline:

1. **Facilitator** shapes raw ideas into crisp user stories
2. **Orchestrator** coordinates the implementation team
3. **Architect** designs the blueprint (contracts, boundaries, test scenarios)
4. **Coder** implements following TDD (optional — user chooses the approach)
5. **Reviewer** audits against the blueprint and conventions
6. **TheOpus** is escalated to when the team hits genuinely hard problems

## Installing Agents

### GitHub Copilot CLI

```bash
copilot plugin install phenixita/mfse-swengineering
```

## Contributing

To add or modify an agent:

1. Create or edit the folder under `agents/<agent-name>/`
2. Add/update the `<agent-name>.agent.md` file
3. Update the Available Agents table in this README
