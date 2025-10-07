---
description: Store current progress and notes in context-manager for session continuity
argument-hint: <notes>
allowed-tools: read, bash, context-manager, anytype
---

# Update Context

Store current progress, decisions, and notes in context-manager for future reference and session continuity.

## Arguments
- Optional: Free-form notes about current progress

## Process

### 1. Detect Current Context

**Determine current ticket and branch:**
```bash
# Get current branch
git rev-parse --abbrev-ref HEAD

# Extract ticket ID from branch name
# Example: enhancement/TC-31-admin-dashboard → TC-31
```

**Get current work status:**
```bash
# Check modified files
git status --short

# Check recent commits
git log -1 --oneline

# Check current time
```

**Display detected context:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 CURRENT CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 Ticket: {ticket-id}
🌿 Branch: {branch-name}
⏰ Current Time: {current-time}

📝 Modified Files ({count}):
{list-modified-files}

📅 Last Commit: {last-commit-message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Retrieve Existing Context

```
context-manager, retrieve current context for {ticket-id}.
```

**Display existing context if found:**
```
📚 EXISTING CONTEXT:

Started: {start-time}
Status: {in-progress/blocked/testing/etc}
Completed Tasks:
{list-completed-tasks}

Previous Notes:
{previous-notes}
```

### 3. Gather Progress Information

**Ask user for current status:**
```
What's the current status?

1. ✅ Task completed
2. 🚧 In progress
3. 🔴 Blocked
4. 🧪 Testing
5. 📝 Needs review
6. ⏸️  Paused
7. 💭 Planning/Research
```

**If blocked, ask for blocker details:**
```
What's blocking progress?

Common blockers:
- Waiting for design approval
- Dependency on another ticket
- Technical issue (specify)
- Need clarification on requirements
- External service unavailable
```

### 4. Collect Task Updates

**If TODO list exists from /start-ticket, show it:**
```
📋 TASK CHECKLIST:

- [ ] Task 1 (Est: 15m)
- [ ] Task 2 (Est: 30m)
- [x] Task 3 (Est: 45m) ← Completed
- [ ] Task 4 (Est: 20m)

Mark completed tasks (comma-separated numbers, e.g., "1,3,4"):
```

**Update task status based on user input.**

### 5. Record Implementation Decisions

**Ask user if there are any important decisions to record:**
```
Any key decisions or approaches to document?

Examples:
- "Used dual submit pattern for draft/publish"
- "Chose to implement RCON with mctools library"
- "Added is_draft boolean instead of status enum"
- "Decided to use Pillow for thumbnail generation"

Enter decisions (or press Enter to skip):
```

### 6. Capture Technical Notes

**Ask for technical details:**
```
Any technical notes to record?

Examples:
- "Migration requires server_default on is_draft field"
- "Upload validation uses PIL.Image.open() for security"
- "Admin routes in new routes_admin.py blueprint"
- "RCON connection timeout set to 10 seconds"

Enter notes (or press Enter to skip):
```

### 7. Check for Issues/Blockers

**Ask about any issues encountered:**
```
Any issues or challenges encountered?

Examples:
- "Jinja2 syntax doesn't work in HTML attributes - used conditional blocks"
- "Docker migration required restart: docker-compose down && up --build"
- "Template rendering broke with duolingo buttons - needed <button> not <a>"

Enter issues (or press Enter to skip):
```

### 8. Estimate Remaining Work

**If task not complete:**
```
Estimate remaining work:

1. < 30 minutes
2. 30m - 1h
3. 1h - 2h
4. 2h - 4h
5. 4h+
6. Unknown/needs investigation
```

### 9. Update Anytype (If Applicable)

**Ask if Anytype should be updated:**
```
Update Anytype with implementation notes?

Options:
1. Yes - Create/update "{ticket-id} Claude Instruction"
2. Yes - Create new note
3. No - Only store in context-manager
```

**If user chooses to update Anytype:**
```
anytype:create_object or anytype:update_object with:
- Title: "{ticket-id} Implementation Notes"
- Type: "Claude Instruction"
- Content: {gathered-notes-and-decisions}
- Tags: {ticket-id}, implementation, {status}
```

### 10. Store in Context-Manager

**Compile all information and store:**

```
context-manager, update {ticket-id} progress:

Session Info:
- Current time: {timestamp}
- Branch: {branch-name}
- Status: {selected-status}
- Blocker: {blocker-info-if-any}

Progress:
- Completed tasks: {list}
- Remaining tasks: {list}
- Estimated remaining time: {estimate}

Decisions Made:
{list-of-decisions}

Technical Notes:
{list-of-technical-notes}

Issues Encountered:
{list-of-issues}

Files Modified:
{list-of-modified-files}

Next Steps:
{inferred-or-user-provided-next-steps}
```

**Display confirmation:**
```
✅ Context updated successfully!

📝 Summary stored:
- Status: {status}
- Progress: {X/Y tasks completed}
- Remaining: {estimate}
- Notes: {count} items recorded

🔍 Retrieve anytime with:
  context-manager, retrieve {ticket-id} progress
```

### 11. Suggest Next Actions

**Based on status, suggest next steps:**

**If In Progress:**
```
💡 SUGGESTED NEXT STEPS:

1. Continue with remaining tasks
2. Run /review-changes when ready
3. Use /commit-ticket when feature complete
```

**If Blocked:**
```
🔴 TICKET BLOCKED

Suggested actions:
1. Document blocker in JIRA ticket
2. Switch to another ticket
3. Reach out to unblock: {blocker-details}
4. Store current work: git stash or commit WIP
```

**If Testing:**
```
🧪 TESTING PHASE

Suggested actions:
1. Run test suite
2. Manual testing checklist
3. Run /review-changes for automated checks
4. Fix any issues found
5. Use /commit-ticket when tests pass
```

**If Needs Review:**
```
📝 READY FOR REVIEW

Suggested actions:
1. Run /review-changes for automated review
2. Fix any critical issues
3. Use /commit-ticket to create commit
4. Push and create PR
```

## Special Cases

### End of Day Context Save

**If it's end of work day:**
```
🌙 END OF DAY SAVE

Storing complete session state:
- All open tasks
- Work in progress
- Tomorrow's starting point
- Any blockers to address

Tomorrow, use: context-manager, retrieve {ticket-id} progress
```

### Sprint Planning Context

**If multiple tickets:**
```
📊 SPRINT CONTEXT

Current Sprint:
- Active ticket: {ticket-id}
- Completed: {list}
- Blocked: {list}
- Next up: {list}

Store as sprint snapshot? (y/n)
```

### Context Cleanup

**If ticket is complete:**
```
✅ Ticket {ticket-id} complete!

Options:
1. Archive context (keep for reference)
2. Delete context (no longer needed)
3. Keep active (still making changes)
```

## Notes

- Automatically detects current ticket from branch name
- Preserves session state across work periods
- Integrates with Anytype for persistent documentation
- Task checklist from /start-ticket is updated
- Decisions and notes stored for future reference
- Can be run multiple times during development
- Useful for end-of-day saves and handoffs
- Context retrieved by /start-ticket for continuity

## Usage Examples

**Quick update:**
```
/update-context Making good progress, about 30 min left
```

**Detailed update with prompts:**
```
/update-context
→ Follows all prompts for comprehensive update
```

**End of day:**
```
/update-context End of day save, will continue tomorrow
```

**Blocker:**
```
/update-context Blocked waiting for DB schema approval
```

## Related Commands

- `/start-ticket` - Retrieves context at start
- `/commit-ticket` - Updates context on commit
- `/review-changes` - Stores review results
- `/update-docs` - Updates documentation