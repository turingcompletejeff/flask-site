---
description: Commit ticket work with automatic time tracking and JIRA Smart Commits
argument-hint: <ticket-id> [--close]
allowed-tools: bash, read, time, code-reviewer, context-manager
---

# Commit JIRA Ticket

Commit completed work with automatic time calculation, code review, and JIRA Smart Commit format.

## Arguments
- JIRA ticket ID (e.g., TC-31)
- Optional: `--close` flag to mark ticket as done in JIRA

## Process

### 1. Retrieve Start Time from Context

```
context-manager, retrieve {ticket-id} session start time.
```

**If start time not found, ask user for approximate start time.**

### 2. Get Current Time

Use `time:get_datetime` tool to get current time in America/New_York timezone.

### 3. Calculate Elapsed Time

**Time calculation:**
1. Calculate difference: end_time - start_time
2. Convert to total minutes
3. Round to nearest 15 minutes (JIRA requirement)
4. Format as "Xh Ym" or "Xh" or "Ym"

**Examples:**
- 87 minutes → 90 minutes → "1h 30m"
- 125 minutes → 120 minutes → "2h"
- 42 minutes → 45 minutes → "45m"
- 8 minutes → 15 minutes → "15m"

### 4. Run Pre-Commit Review

```
code-reviewer, analyze all changes for {ticket-id}. Check for:
1. Security vulnerabilities
2. Best practices violations
3. Logic errors or bugs
4. Missing error handling
5. CSRF protection on forms
6. Proper @login_required decorators
7. SQL injection risks (must use ORM)
8. XSS risks (proper escaping)
```

**Display review findings.**

### 5. Check for Review Issues

**If code-reviewer found issues:**
```
⚠️  CODE REVIEW FINDINGS:

{List issues found}

Options:
1. 🔧 Fix issues before committing
2. ⚠️  Commit anyway (not recommended)
3. ❌ Cancel commit

Your choice?
```

**Wait for user decision.**

**If user chooses to fix issues:**
- Pause commit process
- Wait for fixes
- Re-run code-reviewer
- Continue when clean

### 6. Get Staged Changes Summary

```bash
# Check what's staged
git diff --cached --stat

# Get commit file list
git diff --cached --name-only
```

**Display changed files to user.**

### 7. Generate Commit Message

**Ask user for commit description:**
```
Provide a detailed description of what was implemented/fixed:
(This will be used in the #comment portion of the Smart Commit)
```

**Build Smart Commit message:**
```
{ticket-id} #time {calculated-time} #comment {user-description}[--close flag if present]
```

**Examples:**
```bash
# Without --close
TC-31 #time 2h 30m #comment Implemented admin dashboard with user management, role-based access controls, and activity logging

# With --close
TC-4 #time 1h 45m #comment Added draft functionality with is_draft field, dual submit buttons, and visibility controls #close
```

### 8. Preview and Confirm

**Show commit preview:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 COMMIT PREVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 TICKET: {ticket-id}
⏰ TIME WORKED: {calculated-time}
   Started: {start-time}
   Ended: {end-time}
   Elapsed: {actual-minutes} min → {rounded-minutes} min

📋 COMMIT MESSAGE:
{full-smart-commit-message}

📁 FILES CHANGED ({count}):
{list-of-changed-files}

✅ CODE REVIEW: {PASSED / WARNINGS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proceed with commit? (y/n)
```

### 9. Execute Commit

**If user confirms:**
```bash
git commit -m "{smart-commit-message}"
```

**Display result:**
```
✅ Commit successful!

📤 Next steps:
1. Push to remote: git push origin {branch-name}
2. Create PR if needed
3. Update Anytype with implementation notes (if applicable)
```

### 10. Update Context Manager

```
context-manager, update {ticket-id} completion:
- Status: Committed
- Time spent: {calculated-time}
- End time: {end-time}
- Commit hash: {get-commit-hash}
- Files changed: {file-list}
- Key changes: {brief-summary}
```

### 11. Cleanup Session Context

```
context-manager, archive {ticket-id} session data for future reference.
```

## Error Handling

**If git commit fails:**
```
❌ Commit failed!

Error: {error-message}

Possible issues:
- Nothing staged (run: git add <files>)
- Merge conflict
- Pre-commit hooks failed
- Repository issues

Please resolve and try again.
```

**If context-manager has no start time:**
```
⚠️  No start time recorded for {ticket-id}.

Please provide approximate start time:
1. Use current session (~X hours ago)
2. Enter specific time (e.g., "2:30 PM")
3. Enter duration directly (e.g., "2h 30m")
```

## Notes

- Time is ALWAYS rounded to nearest 15 minutes for JIRA
- Smart Commit format: `TC-XX #time Xh Ym #comment Description [#close]`
- code-reviewer runs automatically before every commit
- Start time retrieved from context-manager (set by /start-ticket)
- `--close` flag adds `#close` to transition ticket to Done in JIRA
- Commit message description should be detailed but concise

## Related Commands

- `/start-ticket` - Begin ticket with time tracking
- `/review-changes` - Run comprehensive review
- `/update-context` - Store progress notes
- `/update-docs` - Update documentation after feature