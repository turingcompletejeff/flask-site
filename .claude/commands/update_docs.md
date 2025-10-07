---
description: Update project documentation using documentation-expert and api-documenter agents
argument-hint: [--api] [--readme] [--all] [ticket-id]
allowed-tools: read, write, edit, grep, documentation-expert, api-documenter
---

# Update Documentation

Update project documentation after implementing features, using specialized documentation agents.

## Arguments
- Optional: `--api` - Focus on API documentation only
- Optional: `--readme` - Focus on README.md only
- Optional: `--all` - Update all documentation
- Optional: `ticket-id` - Document changes for specific ticket

**Default (no args):** Smart detection based on recent changes

## Process

### 1. Detect Recent Changes

**Analyze recent commits and modifications:**
```bash
# Get recent commits (last 5 or since last tag)
git log -5 --oneline

# Get changed files
git diff --name-only HEAD~5..HEAD

# Get current branch for ticket context
git rev-parse --abbrev-ref HEAD
```

**Categorize changes:**
- 📡 API Changes: New routes, endpoints, request/response formats
- 🏗️ Architecture: New blueprints, models, major refactoring
- ✨ Features: New functionality added
- 🔧 Configuration: New environment variables, settings
- 🐛 Fixes: Bug fixes, corrections
- 📦 Dependencies: New packages in requirements.txt

**Display change summary:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 CHANGE DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Analyzing: Last 5 commits
🎫 Ticket: {ticket-id-if-found}

Changes Detected:
📡 API: {count} new/modified endpoints
🏗️ Architecture: {count} structural changes
✨ Features: {count} new features
🔧 Config: {count} configuration changes
📦 Dependencies: {count} new packages

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Determine Documentation Scope

**Based on flags and detected changes:**

**If `--api` flag or API changes detected:**
- ✅ Use `api-documenter` agent
- Update API documentation
- Generate OpenAPI/endpoint specs

**If `--readme` flag or major features added:**
- ✅ Use `documentation-expert` agent
- Update README.md
- Update feature list

**If `--all` flag:**
- ✅ Use both `api-documenter` AND `documentation-expert`
- Comprehensive documentation update

**Display documentation plan:**
```
📝 DOCUMENTATION PLAN

Agents to use:
{list-of-agents}

Files to update:
{list-of-documentation-files}

Proceed? (y/n)
```

### 3. Run api-documenter (If Applicable)

**If API changes detected or --api flag:**

```
api-documenter, analyze and document the following API changes:

## Changed Routes:
{list-of-modified-routes-from-git-diff}

## Task:
1. Analyze new/modified routes in:
   - app/routes.py
   - app/routes_auth.py
   - app/routes_blogpost.py
   - app/routes_mc.py
   - Any new route files

2. Document for each endpoint:
   - HTTP method and path
   - Authentication requirements
   - Request parameters (query, body, form)
   - Request body schema (if applicable)
   - Response format and status codes
   - Error responses
   - Example requests/responses
   - CSRF requirements

3. Update or create:
   - API.md (endpoint reference)
   - OpenAPI/Swagger spec (if needed)
   - Postman collection (if applicable)

4. Follow project patterns:
   - Blueprint organization
   - Flask-Login authentication
   - WTForms for forms
   - CSRF protection details
```

**api-documenter output location:**
- Create/update: `docs/API.md`
- Create/update: `docs/openapi.yml` (if OpenAPI needed)

**Display api-documenter results:**
```
📡 API DOCUMENTATION UPDATED

Files modified:
{list-of-files}

New endpoints documented: {count}
Updated endpoints: {count}

Preview: {snippet-of-api-docs}
```

### 4. Run documentation-expert (If Applicable)

**If README update needed or --readme/--all flag:**

```
documentation-expert, update project documentation based on recent changes:

## Context:
- Ticket: {ticket-id}
- Recent commits: {commit-list}
- New features: {feature-list}
- Changed files: {file-list}

## Files to Review and Update:

### README.md
Sections to check/update:
- Features list (add new features)
- Installation steps (if dependencies changed)
- Configuration (if new env vars added)
- Usage examples (if new functionality added)
- Project structure (if new files/folders added)

### CLAUDE.md
Update if project patterns changed:
- New coding conventions
- New architecture patterns
- New database models
- New important patterns
- New development best practices

### Other Documentation
- CHANGELOG.md (if exists) - Add recent changes
- CONTRIBUTING.md (if exists) - Update if workflow changed
- docs/ folder - Update any relevant guides

## Requirements:
1. Keep existing structure and tone
2. Be concise but comprehensive
3. Include code examples where helpful
4. Update version numbers if applicable
5. Maintain markdown formatting consistency
6. Cross-reference related documentation

## Specific Updates Needed:
{list-specific-updates-based-on-changes}

Example updates:
- "Added draft post functionality" → Update Features section
- "New RCON integration" → Add to Features and Configuration
- "New duolingo-draft button class" → Add to Coding Conventions
- "New environment variable UPLOAD_FOLDER" → Add to Configuration
```

**documentation-expert output:**

**Display changes preview:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 DOCUMENTATION UPDATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

README.md:
+ Added "Draft Posts" to Features section
+ Updated Configuration with new UPLOAD_FOLDER variable
+ Added usage example for draft functionality

CLAUDE.md:
+ Added draft post pattern to Important Patterns
+ Updated Database Models with is_draft field
+ Added duolingo-draft button class to conventions

CHANGELOG.md:
+ Added entry for {ticket-id}: {description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5. Review Documentation Changes

**Show diff of documentation updates:**
```bash
# Show changes to documentation files
git diff README.md
git diff CLAUDE.md
git diff docs/API.md
```

**Present for review:**
```
📝 DOCUMENTATION DIFF

{show-colorized-diff-of-changes}

Changes look good? 
1. ✅ Accept all changes
2. ✏️  Edit specific files before accepting
3. ❌ Discard changes and redo
4. 💾 Accept and commit separately
```

### 6. Handle Special Documentation

**If specific documentation types are detected:**

**Migrations:**
```
🗄️ DATABASE MIGRATION DETECTED

documentation-expert, create migration documentation:

File: docs/migrations/{timestamp}-{description}.md

Include:
- Migration purpose
- Schema changes
- Upgrade procedure
- Rollback procedure
- Data migration notes (if any)
- Testing steps
```

**New Features:**
```
✨ NEW FEATURE DETECTED

documentation-expert, create feature documentation:

File: docs/features/{feature-name}.md

Include:
- Feature overview
- User guide
- API endpoints (if applicable)
- Configuration options
- Examples
- Troubleshooting
```

**Security Changes:**
```
🔐 SECURITY-RELATED CHANGES DETECTED

documentation-expert, update security documentation:

File: docs/SECURITY.md

Include:
- New security measures
- Updated authentication flow
- Changed authorization rules
- Security best practices
- Vulnerability fixes (if applicable)
```

### 7. Generate Changelog Entry

**If CHANGELOG.md exists:**
```
documentation-expert, create changelog entry:

## Version: {next-version or Unreleased}
Date: {current-date}
Ticket: {ticket-id}

### Added
{list-new-features}

### Changed
{list-changes}

### Fixed
{list-bug-fixes}

### Security
{list-security-updates}

Follow Keep a Changelog format: https://keepachangelog.com/
```

### 8. Update Code Comments/Docstrings

**If significant code changes:**
```
documentation-expert, review and update inline documentation:

Files to check:
{list-of-modified-python-files}

Ensure:
- Module docstrings present
- Function docstrings follow Google/NumPy style
- Complex logic has explanatory comments
- TODOs are tracked
- Type hints where applicable (Python 3.6+)

Example:
def create_post(title: str, content: str, is_draft: bool = False) -> BlogPost:
    """
    Create a new blog post.
    
    Args:
        title: Post title
        content: Post content in markdown
        is_draft: Whether to save as draft (default: False)
        
    Returns:
        BlogPost: The created blog post instance
        
    Raises:
        ValueError: If title or content is empty
    """
```

### 9. Commit Documentation Changes

**Ask user about committing documentation:**
```
💾 COMMIT DOCUMENTATION?

Options:
1. 📦 Commit with feature (amend to last commit)
2. 📝 Separate documentation commit
3. ⏸️  Stage but don't commit (manual commit later)
4. ❌ Discard documentation changes

Your choice?
```

**If separate commit chosen:**
```bash
# Stage documentation files
git add README.md CLAUDE.md docs/ CHANGELOG.md

# Create commit
git commit -m "docs: Update documentation for {ticket-id}

- Updated README.md with new features
- Added API documentation for new endpoints
- Updated CLAUDE.md with new patterns
- Added changelog entry

Related to {ticket-id}"
```

**If amend chosen:**
```bash
# Add to last commit
git add README.md CLAUDE.md docs/ CHANGELOG.md
git commit --amend --no-edit
```

### 10. Generate Documentation Report

**Create summary report:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DOCUMENTATION UPDATE REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 Ticket: {ticket-id}
📅 Date: {current-date}
🤖 Agents Used: {list-of-agents}

📝 Files Updated ({count}):
- README.md
- CLAUDE.md
- docs/API.md
- CHANGELOG.md

✅ Documentation Tasks:
- [x] API endpoints documented
- [x] README features updated
- [x] Configuration documented
- [x] Code examples added
- [x] Changelog entry created

📊 Statistics:
- Lines added: {count}
- Lines modified: {count}
- New sections: {count}
- Updated endpoints: {count}

💾 Commit Status: {committed/staged/unstaged}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 11. Store Documentation Context

**Save in context-manager:**
```
context-manager, store documentation update for {ticket-id}:
- Files updated: {list}
- Agents used: {list}
- Timestamp: {current-time}
- Commit hash: {hash-if-committed}
- Changes summary: {brief-summary}
```

## Documentation Templates

### API Endpoint Template (api-documenter)

```markdown
### POST /post/new

Create a new blog post.

**Authentication:** Required (`@login_required`)

**Request:**
- Content-Type: `multipart/form-data`
- CSRF Token: Required

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| title | string | Yes | Post title |
| content | string | Yes | Post content (Markdown) |
| portrait | file | No | Portrait image (JPEG/PNG) |
| is_draft | boolean | No | Save as draft (default: false) |

**Response (Success):**
- Status: 302 (Redirect to index)
- Flash: "post created!" (success)

**Response (Error):**
- Status: 200 (Form re-render with errors)
- Form validation errors displayed

**Example:**
\`\`\`bash
curl -X POST http://localhost:5000/post/new \
  -H "Cookie: session=..." \
  -F "title=My Post" \
  -F "content=This is my post content" \
  -F "portrait=@image.jpg" \
  -F "is_draft=false"
\`\`\`

**Security:**
- CSRF protection enabled
- Login required
- File upload validation with `secure_filename()`
- Image validation via PIL
```

### Feature Documentation Template (documentation-expert)

```markdown
# Feature Name

## Overview
Brief description of the feature and its purpose.

## Usage

### Basic Example
\`\`\`python
# Code example
\`\`\`

### Advanced Example
\`\`\`python
# More complex usage
\`\`\`

## Configuration

Required environment variables:
- `VAR_NAME`: Description

## API Endpoints

- `GET /endpoint` - Description
- `POST /endpoint` - Description

## Database Schema

\`\`\`python
class Model(db.Model):
    # Fields
\`\`\`

## Security Considerations

- Authentication requirements
- Authorization rules
- Input validation

## Troubleshooting

### Common Issue 1
**Problem:** Description
**Solution:** How to fix

## Related

- Link to related features
- Link to related documentation
```

## Special Cases

### First Time Documentation

**If no API.md exists:**
```
📄 CREATING NEW API DOCUMENTATION

api-documenter will create comprehensive API documentation
from scratch by analyzing all routes in:
- app/routes.py
- app/routes_auth.py
- app/routes_blogpost.py
- app/routes_mc.py

This may take a moment...
```

### Undocumented Routes

**If routes found without documentation:**
```
⚠️  UNDOCUMENTED ROUTES FOUND ({count})

The following routes have no documentation:
- POST /route/path
- GET /another/route

Add documentation for these routes? (y/n)
```

### Outdated Documentation

**If documentation conflicts with code:**
```
❌ DOCUMENTATION MISMATCH DETECTED

API.md documents endpoint:
  POST /old/endpoint

But route file shows:
  POST /new/endpoint

Update documentation to match code? (y/n)
```

## Notes

- Uses `api-documenter` for API endpoint documentation
- Uses `documentation-expert` for README, guides, and general docs
- Automatically detects what needs updating based on recent changes
- Can update all docs with `--all` flag
- Supports separate documentation commits
- Stores documentation context in context-manager
- Generates changelog entries automatically
- Validates documentation against actual code

## Related Commands

- `/start-ticket` - Begin ticket (may need docs after)
- `/commit-ticket` - Commit feature (run /update-docs after)
- `/review-changes` - May suggest documentation updates
- `/update-context` - Store documentation status