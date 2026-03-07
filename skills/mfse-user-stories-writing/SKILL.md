---
name: MFSE-user-stories-writing
description: 'Create effective User Stories with step-by-step guidance. Use when: drafting new features, documenting requirements, writing acceptance criteria in standard BDD format (Given/When/Then). Generates complete, properly formatted User Stories.'
argument-hint: 'Requirement to write as a User Story'
---

# Azure DevOps User Story Creation

Create complete, well-structured User Stories following industry best practices. This skill guides you through each component and generates ready-to-use content.

## When to Use

- Writing new feature requirements for a product backlog
- Documenting user-facing functionality that needs acceptance criteria
- Converting requirements into properly formatted User Stories
- Creating epics or nested stories with consistent structure

## Before You Start

Gather these details about your feature:
- Who uses this feature (user type/persona)
- What they want to accomplish (goal or outcome)
- Why they need it (business value or reason)
- Success criteria (testable conditions that prove completion)

## Step-by-Step Procedure

### 1. Define the User Persona
Identify the type of user: team member, admin, customer, stakeholder, etc.

Example:
- Product Manager
- Development Team Lead
- End-user / Customer

### 2. Write the User Story Statement
Use the standard format you can find in the [reference](../MFSE-user-stories-writing/references/REFERENCE.md).


Best Practices:
- Each criterion should be testable
- Write from a user perspective, not technical implementation
- Include both happy path and edge cases
- Use consistent language
- Follow INVEST principles (Independent, Negotiable, Valuable, Estimable, Small, Testable)

### 4. Add Supporting Details (Optional)

Include if relevant:
- Dependencies: What must be completed first?
- Notes: Technical constraints, performance targets, compliance requirements
- Related Stories: Links to other stories / features / epics that are connected


### 5. Output

Once complete, your User Story is ready to:
- Share with user


## Tips for Success

1. User-centered language: Write for the person using the feature, not developers implementing it
2. Avoid over-specification: Don't prescribe the technical solution
3. Testability first: Every criterion should have a clear pass/fail condition
4. Scenarios over bullets: Gherkin format (Given/When/Then) makes criteria unambiguous
5. Keep it focused: One user story = one user goal; split large features into smaller stories
