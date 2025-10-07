  Agent Usage Analysis

  Meta-Orchestration Agents

  1. agent-organizer
  - Usage: Master coordinator for complex multi-step features; analyzes requirements and assembles
  specialized agent teams
  - Context Needs: Project structure, tech stack, CLAUDE.md file status, architectural patterns
  - Key Pattern: Provides delegation strategy, NOT direct implementation
  - Output: Structured markdown with project analysis, agent team selection, execution plan

  2. context-manager
  - Usage: Central nervous system maintaining project knowledge across sessions
  - Context Needs: Filesystem structure, agent activity logs, recent changes
  - Key Pattern: Maintains context-manager.json with directory tree, purposes, timestamps
  - Output: JSON-formatted briefings and activity logs

  Development Agents

  3. backend-architect
  - Usage: Consultative design of backend systems, APIs, database schemas
  - Context Needs: Existing architecture, tech stack, API patterns, database design
  - Communication Protocol: MUST query context-manager first, then clarify missing details
  - Output: Architecture docs, API contracts, data schemas with trade-offs explained

  4. python-pro
  - Usage: Advanced Python implementation with performance optimization
  - Context Needs: Python project structure, dependencies, frameworks, existing patterns
  - Communication Protocol: Query context-manager → synthesize → clarify → implement
  - Output: Idiomatic Python code with tests, type hints, docstrings

  5. flask-dev
  - Usage: PLANNING AND ANALYSIS ONLY - project-specific Flask expertise
  - Critical Rule: Never use for direct file writes, only for creating implementation plans
  - Context Needs: Blueprint structure, models, routes, forms, configuration patterns
  - Output: Detailed plans that YOU implement with Edit/Write tools

  6. frontend-developer
  - Usage: React/UI component development with accessibility and performance focus
  - Context Needs: Component library, design system, frontend architecture, styling patterns
  - Communication Protocol: Query context-manager → clarify → implement
  - Output: TypeScript components, tests, accessibility checklist

  Quality Assurance Agents

  7. code-reviewer
  - Usage: Pre-commit comprehensive code review (use immediately after writing code)
  - Context Needs: Coding standards, recent changes, pull request context, quality metrics
  - Communication Protocol: Query context-manager → review against checklist → report
  - Output: Terminal-formatted review with Critical/Warning/Suggestion sections

  8. architect-reviewer
  - Usage: Post-structural-change architectural consistency validation
  - Context Needs: Architectural patterns, design principles, service boundaries
  - Communication Protocol: Query context-manager → assess impact → recommend
  - Output: Impact assessment, pattern compliance checklist, refactoring suggestions

  9. security-auditor
  - Usage: Proactive security assessment for auth, uploads, data access
  - Context Needs: Authentication methods, security configurations, sensitive data handling
  - Communication Protocol: Query context-manager → threat model → audit → remediate
  - Output: Vulnerability reports with severity, reproduction steps, remediation code

  Documentation Agents

  10. documentation-expert
  - Usage: Comprehensive technical documentation and user guides
  - Context Needs: Existing docs, project features, user guides, style standards
  - Communication Protocol: Query context-manager → clarify audience → create
  - Output: User manuals, tutorials, troubleshooting guides, style guides

  11. api-documenter
  - Usage: Developer-first API documentation with OpenAPI specs
  - Context Needs: API endpoints, data models, authentication methods, existing specs
  - Communication Protocol: Query context-manager → clarify endpoints → document
  - Output: OpenAPI 3.0 YAML, code examples, Postman collections

  Critical Patterns for Context Files

  Each subdirectory's context file should include:

  1. Directory Purpose - What this directory contains and why
  2. Key Files - Important files with brief descriptions
  3. Function Signatures - For code files: function name, inputs, outputs, side effects
  4. Patterns to Follow - Coding conventions specific to this directory
  5. Agent Touchpoints - Which agents commonly work here and what they need
  6. Dependencies - Related directories/files that agents should be aware of
  7. Common Tasks - Typical operations performed in this directory
