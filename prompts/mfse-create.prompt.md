---
name: MFSE Create Skill for codebase standards
description: Describe when to use this prompt
---
 
Related skill: `agent-customization`. Load and follow **skills.md** for template and principles.

Follow the `agent-customization` guidelines to create highly effective skills.

Guide the user to create fully-featured skill with SKILL.md, resources, templates and anything relevate.

Leverage progessive context discolusure to guide the future coding agent or LLM that will read the skill with a meaningful usage of descriptions, frontmatter, file links and examples.

Search thourghly the codebase for common patterns and practices in the domain, namespace, project or folder of interest as the user specifies.

If no clear workflow emerges from the conversation, clarify with `ask_tool`:

- What outcome should this skill produce?
- Workspace-scoped or personal?
- Quick checklist or full multi-step workflow?

## Output

A fully featured skill with SKILL.md, resources, templates and anything relevate as specified in SKILL standard by Anthropic.

skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories

## Template for SKILL.md structure

- Frontmatter
- Body

### Frontmatter

| Field           | Required | Constraints                                                                                                       |
| --------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `name`          | Yes      | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen.             |
| `description`   | Yes      | Max 1024 characters. Non-empty. Describes what the skill does and when to use it.                                 |
| `license`       | No       | License name or reference to a bundled license file.                                                              |
| `compatibility` | No       | Max 500 characters. Indicates environment requirements (intended product, system packages, network access, etc.). |
| `metadata`      | No       | Arbitrary key-value mapping for additional metadata.                                                              |
| `allowed-tools` | No       | Space-delimited list of pre-approved tools the skill may use. (Experimental)                                      |

### Body 

The Markdown body after the frontmatter contains the skill instructions. There are no format restrictions. Write whatever helps agents perform the task effectively.
Recommended sections:
Step-by-step instructions
Examples of inputs and outputs
Common edge cases
Note that the agent will load this entire file once it’s decided to activate a skill. Consider splitting longer SKILL.md content into referenced files.