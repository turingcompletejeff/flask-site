---
description: Begin work on a JIRA ticket with proper setup, time tracking, and agent coordination
argument-hint: <ticket-id>
allowed-tools: bash, read, grep, time, anytype
---

# Start JIRA Ticket

Begin work on a JIRA ticket with proper setup, time tracking, context gathering, and agent coordination.

## Arguments
- JIRA ticket ID (e.g., TC-31)

## Process

### 1. Record Start Time
Use `time:get_datetime` tool to automatically record the start time in America/New_York timezone.

**Store the start time for later time calculation.**

### 2. Search Anytype for Ticket Instructions
Search Anytype for "Claude Instruction" objects related to this ticket:
- Search: "{ticket-id} Claude Instruction"
- Search: "{ticket-id} plan"
- Search: "{ticket-id}"

**Display any found instructions prominently.**

### 3. Check Git Status and Create Branch

```bash
# Check current status
git status

# If not on a feature branch, create one
# Branch naming: enhancement/TC-XX-description, bugfix/TC-XX-description, styling/TC-XX-description
git checkout -b enhancement/{ticket-id}-brief-description
```

### 4. Gather Context

**Read project context:**
- Primary: `CLAUDE.md` - Project patterns and conventions
- Ticket-specific: `CLAUDE-{ticket-id}.md` (if exists) - Specific implementation notes
- Related context: Search for similar ticket files

**Analyze codebase:**
- Use `grep` to find related files mentioning similar features
- Check recent commits for related work: `git log --oneline --grep="{ticket-id-prefix}" -n 10`
- Review relevant blueprint files (routes_*.py, models.py, forms.py, templates/)

### 5. Determine Complexity and Agent Strategy

**Assess ticket complexity:**
- **Simple** (1-2 files, < 1 hour): Direct implementation, optional agent assistance
- **Medium** (3-5 files, 1-3 hours): Use specific agents (backend-architect, frontend-developer, etc.)
- **Complex** (6+ files, 3+ hours, multiple systems): Use agent-organizer for coordination

**Recommend agent strategy based on complexity.**

### 6. Create Implementation Plan

**Based on complexity, create appropriate plan:**

**For Simple tickets:**
```
TODO List:
- [ ] Task 1 (Est: 15m)
- [ ] Task 2 (Est: 30m)
- [ ] Review (Est: 15m)

Recommended approach: Direct implementation
Optional agents: code-reviewer (pre-commit)
```

**For Medium tickets:**
```
TODO List:
- [ ] Design Phase (Est: 30m)
  - backend-architect: Design schema/route changes
- [ ] Implementation (Est: 1-2h)
  - python-pro: Implement logic
  - frontend-developer: Update templates
- [ ] Security Review (Est: 15m)
  - security-auditor: Review changes
- [ ] Pre-commit Review (Est: 15m)
  - code-reviewer: Final review

Recommended agents: backend-architect, python-pro, security-auditor, code-reviewer
```

**For Complex tickets:**
```
TODO List:
- [ ] Analysis & Orchestration (Est: 30-45m)
  - agent-organizer: Analyze requirements and create detailed plan
- [ ] Multi-phase Implementation (Est: 2-4h)
  - Phase 1: [Component A] - backend-architect, python-pro
  - Phase 2: [Component B] - frontend-developer, ui-designer
  - Phase 3: [Component C] - security-auditor
- [ ] Integration & Testing (Est: 30m)
  - test-automator: Create tests
- [ ] Architecture Review (Est: 15m)
  - architect-review: Validate patterns
- [ ] Pre-commit Review (Est: 15m)
  - code-reviewer: Final review

Recommended approach: agent-organizer coordination
```

### 7. Display Context Summary

**Present gathered information:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 TICKET: {ticket-id}
⏰ START TIME: {recorded-time}
🌿 BRANCH: enhancement/{ticket-id}-{description}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 ANYTYPE INSTRUCTIONS:
{Display Anytype instructions if found, or "No specific instructions found"}

🎯 COMPLEXITY: {Simple/Medium/Complex}
🤖 RECOMMENDED AGENTS: {List of agents}

📚 RELATED FILES:
- {List of relevant files from grep/analysis}

✅ IMPLEMENTATION PLAN:
{Display appropriate TODO list based on complexity}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 8. Confirm Before Starting

**Ask user:**
```
Ready to begin {ticket-id}?

Options:
1. ✅ Proceed with recommended approach
2. 📝 Modify plan (specify changes)
3. 🤖 Use different agent strategy
4. ⏸️  Review Anytype instructions first
```

**Wait for user approval before proceeding.**

### 9. Initialize Agent(s) if Approved

**Based on user choice:**

**For Simple/Direct approach:**
- No agents needed, proceed with implementation
- Store start time for commit

**For Medium complexity:**
```
Using {specific-agent} to {specific-task}...
```

**For Complex with agent-organizer:**
```
agent-organizer, analyze {ticket-id} requirements from Anytype 
instructions and coordinate implementation.
```

### 10. Store Context for Later

**Save to context-manager:**
```
context-manager, store {ticket-id} session start:
- Start time: {time}
- Branch: {branch-name}
- Complexity: {level}
- Agent strategy: {approach}
- Key context: {important-notes-from-anytype}
```

## Notes

- Always check Anytype first for ticket-specific instructions
- Complexity assessment helps choose right agent coordination level
- Start time stored for automatic time calculation at commit
- Context-manager preserves session state for later retrieval
- User approval required before beginning work
- Agent strategy can be adjusted based on user preference

## Related Commands

- `/commit-ticket` - Commit work with auto time tracking
- `/review-changes` - Run code-reviewer before commit
- `/update-context` - Store progress in context-manager