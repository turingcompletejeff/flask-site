# .claude Directory Context

## Purpose
Claude Code configuration directory containing agent definitions, slash commands, and project-specific settings for AI-assisted development.

## Directory Structure

```
.claude/
├── agents/              - Agent definition files (markdown)
├── commands/            - Slash command definitions (markdown)
└── settings.local.json  - Local permissions and configuration
```

## Agent Definitions (`/agents/`)

Custom agents for this Flask project. See individual agent files for detailed capabilities.

### Meta-Orchestration Agents
- **agent-organizer.md** - Master orchestrator for complex multi-step features
  - Analyzes requirements, assembles agent teams, creates delegation strategy
  - Model: haiku (fast analysis)
  - **Never directly implements** - only provides recommendations

- **context-manager.md** - Project structure and knowledge retention
  - Maintains context-manager.json with filesystem map
  - Tracks agent activity and project state
  - Model: haiku
  - **Critical**: All agents must query this agent first

### Development Agents
- **backend-architect.md** - Flask/Python system design
  - Database schemas, API design, architecture patterns
  - Model: sonnet
  - Communication: MUST query context-manager first

- **python-pro.md** - Advanced Python implementation
  - Performance optimization, design patterns, testing
  - Model: sonnet
  - Communication: MUST query context-manager first

- **flask-dev.md** - Flask-specific expertise
  - **PLANNING ONLY** - Never modifies files directly
  - Model: sonnet
  - Use for: Analysis and detailed implementation plans

- **frontend-developer.md** - UI/UX development
  - React components, Jinja2 templates, jQuery, responsive design
  - Model: sonnet
  - Communication: MUST query context-manager first

### Quality Assurance Agents
- **code-reviewer.md** - Pre-commit code quality review
  - Security, maintainability, best practices, SOLID principles
  - Model: haiku (fast review)
  - Use: Immediately after writing/modifying code

- **architect-review.md** - Architectural consistency validation
  - Design pattern compliance, system integrity
  - Model: haiku
  - Use: After structural changes, new services, API modifications

- **security-auditor.md** - Security assessment
  - Vulnerability scanning, penetration testing, compliance
  - Model: sonnet
  - Use: Proactively for auth, uploads, data access features

### Documentation Agents
- **documentation-expert.md** - Technical documentation
  - User guides, system docs, knowledge bases
  - Model: haiku
  - Communication: MUST query context-manager first

- **api-documenter.md** - API documentation specialist
  - OpenAPI specs, code examples, Postman collections
  - Model: haiku
  - Communication: MUST query context-manager first

## Slash Commands (`/commands/`)

Custom workflow commands for JIRA-driven development.

### /start_ticket <ticket-id>
**Purpose**: Initialize JIRA ticket work with time tracking and context gathering

**Process**:
1. Record start time using `time:get_datetime`
2. Search Anytype for ticket instructions
3. Check git status and create feature branch
4. Display ticket context and instructions
5. Optionally invoke agent-organizer for complex tasks

**Arguments**: JIRA ticket ID (e.g., TC-31)

**Example**:
```
/start_ticket TC-31
```

### /update_context <notes>
**Purpose**: Store progress in context-manager for session continuity

**Process**:
1. Detect current branch and ticket ID
2. Get modified files from git status
3. Report to context-manager with activity summary
4. Optionally update Anytype with progress notes

**Arguments**: Optional free-form progress notes

**Example**:
```
/update_context Implemented user role assignment UI, need to add validation
```

### /review_changes
**Purpose**: Multi-agent comprehensive review before commit

**Process**:
1. Check git status for uncommitted changes
2. Run code-reviewer agent
3. Run architect-reviewer for structural changes
4. Run security-auditor if security-related
5. Summarize findings and recommendations

**Example**:
```
/review_changes
```

### /commit_ticket <ticket-id> [--close]
**Purpose**: Commit with automatic time tracking and JIRA Smart Commits

**Process**:
1. Get current time using `time:get_datetime`
2. Calculate elapsed time from start
3. Round to nearest 15 minutes (JIRA requirement)
4. Generate Smart Commit message
5. Execute git commit with time logging
6. Optionally close ticket with #close flag

**Arguments**:
- ticket-id: JIRA ticket ID
- --close: Optional flag to close ticket

**Smart Commit Format**:
```
TC-XX #time Xh Ym #comment [description] [#close]
```

**Example**:
```
/commit_ticket TC-31 --close
# Generates:
# TC-31 #time 2h 30m #comment Implemented admin dashboard with role management #close
```

### /update_docs [--api] [--readme] [--all] [ticket-id]
**Purpose**: Update documentation using specialized agents

**Process**:
1. Determine documentation scope from flags
2. Invoke documentation-expert for general docs
3. Invoke api-documenter for API specs
4. Update CLAUDE.md if project structure changed
5. Associate with ticket if provided

**Arguments**:
- --api: Update API documentation
- --readme: Update README.md
- --all: Update all documentation
- ticket-id: Optional JIRA ticket to associate

**Example**:
```
/update_docs --api TC-31
```

## Settings (`settings.local.json`)

Local permissions configuration for MCP tools and file access.

### Current Permissions

**Allowed (no user prompt)**:
- `mcp__time__get_datetime` - Time tracking for JIRA
- `mcp__time__what_time_is_it` - Current time queries
- `mcp__time__get_current_time` - Time retrieval
- `Read(//home/shades/git/time-mcp/**)` - Time MCP file access

**Deny**: None

**Ask**: Everything else (default)

### Permission Format
```json
{
  "permissions": {
    "allow": ["pattern1", "pattern2"],
    "deny": ["pattern3"],
    "ask": []
  }
}
```

## Agent Communication Protocol

All development agents follow this protocol:

### 1. Context Acquisition (MANDATORY)
```json
{
  "requesting_agent": "agent-name",
  "request_type": "get_task_briefing",
  "payload": {
    "query": "Initial briefing required for [task]. Provide [context needs]."
  }
}
```

### 2. Clarification (if needed)
Agent synthesizes context and asks ONLY missing questions.

### 3. Implementation/Analysis
Agent performs its specialized task.

### 4. Activity Reporting
```json
{
  "reporting_agent": "agent-name",
  "status": "success",
  "summary": "Brief description of work completed",
  "files_modified": ["/path/to/file1", "/path/to/file2"]
}
```

### 5. Final Summary
Natural language summary to main process.

## Agent Usage Patterns

### Pattern 1: Automatic Multi-Agent (Complex Features)
```
/start_ticket TC-XX
agent-organizer, implement [complex feature] following Anytype instructions.
→ agent-organizer coordinates 4-6 agents automatically
→ You implement based on coordinated plan
/review_changes
/commit_ticket TC-XX --close
```

### Pattern 2: Sequential Single Agents (Focused Changes)
```
backend-architect, design schema for [feature].
→ Review design
python-pro, implement the schema changes.
→ Review implementation
security-auditor, review for access control issues.
→ Address findings
code-reviewer, final review before commit.
```

### Pattern 3: Planning Only (flask-dev)
```
flask-dev, analyze routes_blogpost.py and create a detailed plan for
adding tag functionality. DO NOT modify files.
→ Review plan
→ Implement yourself using Edit/Write tools
```

### Pattern 4: Context Preservation (Between Sessions)
```
# End of day
/update_context Completed TC-4, in progress TC-47 (RCON client implemented)

# Next day
context-manager, what was the status of TC-47?
→ Retrieves stored context
Continue TC-47...
```

## Common Agent Tasks

### Starting a New Feature
1. `/start_ticket TC-XX`
2. Review Anytype instructions
3. Use agent-organizer if complex, or specific agents if focused
4. Implement based on agent guidance
5. `/review_changes`
6. `/commit_ticket TC-XX`

### Pre-Commit Review
```
code-reviewer, analyze all changes for TC-XX and verify:
1. Security implications
2. Best practices adherence
3. CSRF protection where needed
```

### Architecture Review
```
architect-review, validate that TC-XX changes maintain consistency with:
1. Blueprint pattern
2. Separation of concerns
3. Database design patterns
```

### Security Audit
```
security-auditor, review [feature] for common vulnerabilities:
- Authentication/authorization
- Input validation
- File upload security
```

## Agent Touchpoints

### For Agents Working in This Directory

**context-manager**:
- Needs: .claude/agents/ definitions, command definitions
- Common tasks: Understanding available agents, tracking which agents are used
- Key files: All .md files in agents/ and commands/

**agent-organizer**:
- Needs: Agent capabilities from agents/*.md files
- Common tasks: Selecting optimal agent teams, understanding agent strengths
- Key files: All agent definition files

**documentation-expert**:
- Needs: Slash command usage, agent workflow patterns
- Common tasks: Documenting development workflows, creating agent usage guides
- Key files: commands/*.md, CLAUDE.md

## Best Practices

### Agent Selection
1. **Use flask-dev for planning only** - Never for direct implementation
2. **Query context-manager first** - All agents should get project context
3. **Use code-reviewer before every commit** - Catch issues early
4. **Use security-auditor proactively** - Don't wait for security issues
5. **Use agent-organizer for complex tasks** - Let it coordinate specialists

### Slash Command Usage
1. **Always /start_ticket** - Proper time tracking and context gathering
2. **Always /review_changes** - Multi-agent quality gate
3. **Always /commit_ticket** - Automatic JIRA time logging
4. **/update_context frequently** - Preserve progress across sessions
5. **/update_docs when structure changes** - Keep documentation current

### Permission Management
- Add frequently used MCP tools to "allow" list
- Use "deny" for dangerous operations
- Default to "ask" for new tools

## Related Files
- `/CLAUDE.md` - Main project context and workflow documentation
- `/CONTEXT.md` - Root directory context (this pattern)
- `/app/CONTEXT.md` - Application code context
- All subdirectory CONTEXT.md files - Component-specific context

## Time Tracking Integration

### MCP Time Tools
- `mcp__time__get_datetime` - Returns formatted datetime in configured timezone
- Automatically allowed in settings.local.json
- Used by /start_ticket and /commit_ticket commands

### JIRA Smart Commits
Format: `TC-XX #time Xh Ym #comment Description [#close]`

**Time Calculation**:
1. Start time recorded at /start_ticket
2. End time retrieved at /commit_ticket
3. Difference calculated and rounded to nearest 15 minutes
4. Automatically formatted in commit message

## Anytype Integration

### Claude Instruction Objects
Search patterns for ticket context:
- `"{ticket-id} Claude Instruction"`
- `"{ticket-id} plan"`
- `"{ticket-id}"`

### Information Stored
- Acceptance criteria
- Technical constraints
- Design decisions
- Related tickets
- Special considerations

## Future Enhancements

Consider adding:
- Test automation agents
- Deployment agents
- Performance profiling agents
- Custom project-specific agents
- More granular slash commands
- Agent activity logging
