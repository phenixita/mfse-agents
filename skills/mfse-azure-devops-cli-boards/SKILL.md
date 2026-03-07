---
name:  MFSE-azure-devops-cli-boards
description: 'Manage Azure DevOps boards using CLI commands. Use when: creating, updating, or querying work items, boards, and sprints. Generates complete, properly formatted CLI commands for Azure DevOps.'
argument-hint: 'Write this work item to azure devops'
user-invocable: true
---

This Skill helps manage Azure DevOps resources using the Azure CLI with Azure DevOps extension.
 

## Prerequisites

Install Azure CLI and Azure DevOps extension:

```bash
# Install Azure CLI
brew install azure-cli  # macOS
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash  # Linux
pip install azure-cli  # via pip

# Verify installation
az --version

# Install Azure DevOps extension
az extension add --name azure-devops
az extension show --name azure-devops
```

 

## Authentication

### Login to Azure DevOps

```bash
# Interactive login (prompts for PAT)
az devops login --organization https://dev.azure.com/{org}

# Login with PAT token
az devops login --organization https://dev.azure.com/{org} --token YOUR_PAT_TOKEN
```

> **Note:** Use `az boards` for work item operations and `az devops` for organization/project-level operations. Common error: `work-item` is not a subcommand of `az devops`, use `az boards work-item` instead.

### Configure Defaults

```bash
# Set default organization and project
az devops configure --defaults organization=https://dev.azure.com/{org} project={project}

# List current configuration
az devops configure --list

# Enable Git aliases
az devops configure --use-git-aliases true
```
 
## Projects

### List Projects

```bash
az devops project list --organization https://dev.azure.com/{org}
az devops project list --top 10 --output table
```
 

### Show Project Details

```bash
az devops project show --project {project-name} --org https://dev.azure.com/{org}
```
 
## Work Items (Boards)

### Query Work Items

```bash
# WIQL query
az boards query \
  --wiql "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] = 'Active'"

# Query with output format
az boards query --wiql "SELECT * FROM WorkItems" --output table
```

### Show Work Item

```bash
az boards work-item show --id {work-item-id}
az boards work-item show --id {work-item-id} --open
```

### Create Work Item

```bash
# Basic work item
az boards work-item create \
  --title "Fix login bug" \
  --type Bug \
  --assigned-to user@example.com \
  --description "Users cannot login with SSO"

# With area and iteration
az boards work-item create \
  --title "New feature" \
  --type "User Story" \
  --area "Project\\Area1" \
  --iteration "Project\\Sprint 1"

# With custom fields
az boards work-item create \
  --title "Task" \
  --type Task \
  --fields "Priority=1" "Severity=2"

# With discussion comment
az boards work-item create \
  --title "Issue" \
  --type Bug \
  --discussion "Initial investigation completed"

# Open in browser after creation
az boards work-item create --title "Bug" --type Bug --open
```

### Update Work Item

> **Preferred format:** Use **Markdown** for `Description` and `AcceptanceCriteria` content whenever possible.
> If you must use HTML line breaks, use `<br/>`.
>
> **Important — `--fields` quoting rules:**
> - Each field-value pair MUST be a **separate** quoted argument: `--fields "Field1=Value1" "Field2=Value2"`.
> - For multi-line HTML fields (`Description`, `AcceptanceCriteria`), use `<br/>` tags for line breaks.
> - **Do NOT use escaped double quotes (`\"`) inside a `--fields` value** — the Azure CLI parser treats them as argument boundaries and splits the value, causing `"The --fields argument should consist of space separated field=value pairs"` errors.
> - Instead, use **single quotes** (`'`) for any embedded quoting inside field values (e.g., `'Product A'` instead of `\"Product A\"`).
> - On **PowerShell (Windows)**, the outer quotes must be double quotes `"..."` and inner quotes must be single quotes `'...'`.

```bash
# Update state, title, and assignee
az boards work-item update \
  --id {work-item-id} \
  --state "Active" \
  --title "Updated title" \
  --assigned-to user@example.com

# Move to different area
az boards work-item update \
  --id {work-item-id} \
  --area "{ProjectName}\\{Team}\\{Area}"

# Change iteration
az boards work-item update \
  --id {work-item-id} \
  --iteration "{ProjectName}\\Sprint 5"

# Add comment/discussion
az boards work-item update \
  --id {work-item-id} \
  --discussion "Work in progress"

# Update with custom fields
az boards work-item update \
  --id {work-item-id} \
  --fields "Priority=1" "StoryPoints=5"

# Update HTML field with multi-line content (use <br/> and single quotes)
az boards work-item update \
  --id {work-item-id} \
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=Given 'Product A' is active<br/>When the command runs<br/>Then 'Product A' should be inactive"

# Update Acceptance Criteria using Markdown (preferred)
az boards work-item update \
  --id {work-item-id} \
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=### Scenario: Disable products without stock\n- Given a company has 'Product A' and 'Product B'\n- And both products have 0 stock\n- When the 'Disable All Products' command is executed\n- Then 'Product A' and 'Product B' should be marked as Inactive"
```

### Concrete Examples

```bash
# Create a User Story with description and Acceptance Criteria (PowerShell safe quoting)
az boards work-item create \
  --title "Bulk Deactivation of Products" \
  --type "User Story" \
  --area "MFSE" \
  --description "As a Company Administrator, I want to disable all products in my catalog at once, so that I can quickly suspend operations." \
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=Scenario: Disable products without stock<br/>Given a company has 'Product A' (Active) and 'Product B' (Active)<br/>And both products have 0 stock<br/>When the 'Disable All Products' command is executed<br/>Then 'Product A' and 'Product B' should be marked as Inactive"

# Update Acceptance Criteria on an existing work item (multi-line HTML field)
az boards work-item update \
  --id 991 \
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=Scenario: Skip products with stock<br/>Given a company has 'Product A' (0 stock) and 'Product B' (5 stock)<br/>When the 'Disable All Products' command is executed<br/>Then 'Product A' should be inactive<br/>But 'Product B' should remain active"

# Add a discussion note and move to Active
az boards work-item update \
  --id 991 \
  --state "Active" \
  --discussion "Ready for implementation."
```

### Delete Work Item

```bash
# Soft delete (can be restored)
az boards work-item delete --id {work-item-id} --yes

# Permanent delete
az boards work-item delete --id {work-item-id} --destroy --yes
```

### Work Item Relations

```bash
# List relations
az boards work-item relation list --id {work-item-id}

# List supported relation types
az boards work-item relation list-type

# Add relation
az boards work-item relation add --id {work-item-id} --relation-type parent --target-id {parent-id}

# Remove relation
az boards work-item relation remove --id {work-item-id} --relation-id {relation-id}
```
 

## Enhanced Global Arguments

| Parameter            | Description                                                |
| -------------------- | ---------------------------------------------------------- |
| `--help` / `-h`      | Show command help                                          |
| `--output` / `-o`    | Output format (json, jsonc, none, table, tsv, yaml, yamlc) |
| `--query`            | JMESPath query string for filtering output                 |
| `--verbose`          | Increase logging verbosity                                 |
| `--debug`            | Show all debug logs                                        |
| `--only-show-errors` | Only show errors, suppress warnings                        |
| `--subscription`     | Name or ID of subscription                                 |
| `--yes` / `-y`       | Skip confirmation prompts                                  |

## Enhanced Common Parameters

| Parameter                  | Description                                                         |
| -------------------------- | ------------------------------------------------------------------- |
| `--org` / `--organization` | Azure DevOps organization URL (e.g., `https://dev.azure.com/{org}`) |
| `--project` / `-p`         | Project name or ID                                                  |
| `--detect`                 | Auto-detect organization from git config                            |
| `--yes` / `-y`             | Skip confirmation prompts                                           |
| `--open`                   | Open resource in web browser                                        |
| `--subscription`           | Azure subscription (for Azure resources)                            |

## Getting Help

```bash
# General help
az devops --help

# Help for specific command group
az pipelines --help
az repos pr --help

# Help for specific command
az repos pr create --help 
```