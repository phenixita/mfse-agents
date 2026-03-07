# Acceptance criteria

Given when then with Gherkin Syntax and scenarios.

```gherkin
Scenario: [Clear scenario title]
- Given [initial state/context]
- When [action user takes]
- Then [expected outcome]

Scenario: [Another scenario]
- Given [initial state]
- When [action]
- Then [expected outcome]
```

## Common Patterns

### Feature with Variations

When a feature has multiple paths or options:

```gherkin
Scenario: User logs in with valid credentials
- Given user is on the login page
- When user enters valid email and password
- Then user is redirected to dashboard

Scenario: User attempts login with invalid credentials
- Given user is on the login page
- When user enters invalid email or password
- Then error message is displayed
```

```gherkin
Scenario Outline: create product with valid price

Given the vending machine is available
When I create a product with code <product_code> and price <price>
Then the product <product_code> is created with price <price>

Examples:
  | product_code | price |
  | COLA         | 1.50  |
  | WATER        | 1.00  |
  | JUICE        | 2.00  |
```

### Integration Stories

When a story involves multiple systems:

```gherkin
Scenario: Data syncs from external API
- Given external API is available
- When sync job runs
- Then all new records are imported without duplicates
```

### Performance or Quality Stories

When criteria focus on non-functional requirements:

```gherkin
Scenario: Dashboard loads efficiently
- Given user navigates to dashboard
- When page elements finish loading
- Then page load time is under 2 seconds
```
