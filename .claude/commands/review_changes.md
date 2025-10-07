---
description: Run comprehensive multi-agent review before committing changes
allowed-tools: read, grep, code-reviewer, security-auditor, architect-review
---

# Review Changes

Run a comprehensive multi-agent review of all changes before committing.

## Process

### 1. Detect Changed Files

```bash
# Get all changed files (staged and unstaged)
git diff --name-only HEAD
git diff --cached --name-only

# Get file statistics
git diff --stat HEAD
```

**Categorize changes:**
- Backend: `app/*.py`, `config.py`
- Frontend: `app/templates/*.html`, `app/static/**/*`
- Database: `migrations/`, `app/models.py`
- Configuration: `*.yml`, `*.json`, `.env.*`, `requirements.txt`
- Documentation: `*.md`, `docs/`

### 2. Determine Review Scope

**Based on changed files, determine which agents are needed:**

**Always run:**
- ✅ `code-reviewer` - General code quality and best practices

**Conditional agents:**
- 🔐 `security-auditor` - If auth, uploads, or user data handling changed
  - Triggers: `routes_auth.py`, `models.py` (User), file upload code, CSRF changes
- 🏗️ `architect-review` - If blueprint structure or architecture changed
  - Triggers: New blueprint files, `app/__init__.py`, major route refactoring
- ⚠️ Special checks - If specific patterns detected
  - Database migrations: Check for `server_default` on non-nullable columns
  - Forms: Verify CSRF tokens present
  - Templates: Check for XSS escaping

**Display review plan:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 REVIEW PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Files Changed: {count}
{list-by-category}

🤖 Agents Needed:
{list-of-agents-with-reasons}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. Run code-reviewer (Always)

```
code-reviewer, analyze all changes. Check for:

## General Code Quality
- PEP 8 compliance
- Proper error handling
- Code duplication
- Dead code or unused imports
- Meaningful variable names
- Proper logging

## Flask-Specific Patterns
- Blueprint registration correct
- Route decorators proper (@login_required, @csrf.exempt)
- URL generation uses url_for()
- Config from environment variables
- No hardcoded secrets

## Database & ORM
- Using SQLAlchemy ORM (no raw SQL)
- Proper relationships defined
- Migrations include server_default for non-nullable fields
- No N+1 query issues

## Templates
- CSRF tokens in forms ({{ form.hidden_tag() }})
- Proper Jinja2 escaping (|safe only when needed)
- No Jinja2 in HTML attributes
- Button classes use duolingo-* styles

## Common Mistakes
- Double-commits (commit after flash message)
- Missing db.session.commit()
- Improper exception handling
- File handle leaks
```

**Display code-reviewer findings.**

### 4. Run security-auditor (If Applicable)

**If auth, uploads, or sensitive data handling changed:**

```
security-auditor, perform security review focusing on:

## Authentication & Authorization
- @login_required on protected routes
- current_user checks for resource ownership
- Password hashing uses bcrypt
- Session security configured

## Input Validation
- File upload validation
  - secure_filename() used
  - File type checking
  - File size limits enforced
- Form validation with WTForms
- SQL injection prevention (ORM only)

## CSRF Protection
- Forms have CSRF tokens
- CSRF exempt only for read-only/public endpoints
- Proper CSRF error handling

## XSS Prevention
- Template escaping enabled
- |safe only for trusted content
- User input sanitized before display

## File Upload Security
- Uploads to configured directory only
- Filename sanitization
- Content-type validation
- PIL/Image validation for images
- File permissions secure

## Data Exposure
- Error messages don't leak sensitive info
- Logs don't contain passwords/secrets
- Environment variables for secrets
- No debug mode in production

## RCON Security (If applicable)
- RCON password from environment
- Command validation
- Connection error handling
```

**Display security-auditor findings.**

### 5. Run architect-review (If Applicable)

**If blueprint structure or architecture changed:**

```
architect-review, validate architectural consistency:

## Blueprint Architecture
- Blueprints properly organized by feature
- Blueprint naming consistent (feature_bp)
- Routes use blueprint url_for()
- Blueprint registration in app/__init__.py

## Separation of Concerns
- Routes handle HTTP only
- Business logic in models or services
- Database queries through ORM
- Templates for presentation only

## Code Organization
- Related routes in same blueprint
- Models organized logically
- Forms in separate forms.py
- Configuration in config.py

## Design Patterns
- Factory pattern for app creation
- Blueprint pattern for routes
- ORM pattern for database
- WTForms for validation

## Dependencies
- Circular import prevention
- Proper module structure
- Dependencies injected properly
```

**Display architect-review findings.**

### 6. Aggregate Results

**Compile all findings:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 REVIEW RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Agents Run: {count}
📁 Files Reviewed: {count}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 CRITICAL ISSUES ({count})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{list-critical-issues}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  WARNINGS ({count})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{list-warnings}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ PASSED CHECKS ({count})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{list-passed-checks}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 7. Provide Recommendations

**Based on severity:**

**If CRITICAL issues found:**
```
🛑 CRITICAL ISSUES DETECTED

You must fix these issues before committing:

{detailed-list-with-file-locations-and-fixes}

Recommended actions:
1. Fix each critical issue
2. Run /review-changes again
3. Proceed with commit once clean
```

**If only WARNINGS found:**
```
⚠️  WARNINGS FOUND

Consider addressing these issues:

{detailed-list-with-file-locations}

Options:
1. 🔧 Fix warnings before commit (recommended)
2. 📝 Document why warnings are acceptable
3. ⏭️  Proceed with commit (warnings will be noted)
```

**If all checks passed:**
```
✅ ALL CHECKS PASSED

Your code looks good! Review summary:

{summary-of-what-was-checked}

Ready to proceed with:
- /commit-ticket {ticket-id}
- git commit -m "..."
```

### 8. Save Review Report

**Store review results in context-manager:**
```
context-manager, store review results for current changes:
- Timestamp: {current-time}
- Files reviewed: {file-list}
- Agents used: {agent-list}
- Critical issues: {count}
- Warnings: {count}
- Status: {PASSED/NEEDS_FIXES}
- Details: {summary}
```

### 9. Offer Quick Fixes

**If common issues detected, offer automated fixes:**

**Example quick fixes:**
```
🔧 QUICK FIXES AVAILABLE:

1. Add missing CSRF tokens to forms
2. Add @login_required to unprotected routes
3. Fix import ordering (PEP 8)
4. Add missing docstrings
5. Replace hardcoded values with config

Apply quick fixes? (y/n for each, or 'all')
```

## Special Checks

### Migration Review
**If migration files changed:**
```
🗄️ MIGRATION DETECTED

Checking migrations/versions/*.py:
- Non-nullable columns have server_default? ✓/✗
- Proper upgrade/downgrade functions? ✓/✗
- Foreign key constraints defined? ✓/✗
- Index creation included? ✓/✗

Recommendation: Test migration with:
  docker-compose exec flask-site flask db upgrade
  docker-compose exec flask-site flask db downgrade
  docker-compose exec flask-site flask db upgrade
```

### Form Review
**If forms changed:**
```
📝 FORM CHANGES DETECTED

Checking app/forms.py and templates:
- WTForms validators present? ✓/✗
- CSRF tokens in templates? ✓/✗
- Form rendering uses macros? ✓/✗
- Error handling implemented? ✓/✗
```

### Upload Review
**If upload logic changed:**
```
📤 UPLOAD LOGIC DETECTED

Checking file upload security:
- secure_filename() used? ✓/✗
- File type validation? ✓/✗
- File size limits enforced? ✓/✗
- Upload directory properly configured? ✓/✗
- PIL validation for images? ✓/✗
```

## Notes

- Always runs code-reviewer for general quality
- Conditionally runs security-auditor and architect-review based on changes
- Critical issues MUST be fixed before committing
- Warnings can be addressed or documented
- Review results stored in context-manager for reference
- Can be run multiple times as fixes are applied

## Related Commands

- `/start-ticket` - Begin ticket with proper setup
- `/commit-ticket` - Commit with auto time tracking (runs this automatically)
- `/update-context` - Store progress notes
- `/update-docs` - Update documentation