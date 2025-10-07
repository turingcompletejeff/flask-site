# Flask Portfolio Site - Project Context

## Architecture
- Flask web framework with Blueprint architecture
- PostgreSQL database via SQLAlchemy ORM
- Gunicorn WSGI server for production
- Docker containerization with Portainer orchestration

## Environment Variables
Required configuration via environment variables:
- DATABASE_URL: PostgreSQL connection string (required)
- SECRET_KEY: Flask secret key for sessions (falls back to 'dev-key-please-change')
- FLASK_ENV: development or production (optional)

Minecraft RCON Integration:
- RCON_HOST: Minecraft server host for RCON commands
- RCON_PORT: Minecraft RCON port (default: 25575)
- RCON_PASSWORD: Minecraft RCON authentication password

Optional:
- UPLOAD_FOLDER: Override default uploads/blog-posts/ directory

## Coding Conventions
- Follow PEP 8 for Python code
- Use Blueprint pattern for route organization
- Always use environment variables for secrets (never hardcode)
- Database migrations: Use Flask-Migrate (flask db migrate/upgrade)
- Button styling: Use duolingo-buttons.css classes consistently
  - Available classes: duolingo-primary, duolingo-success, duolingo-secondary, duolingo-draft, duolingo-danger
  - Primary: Default actions
  - Success: Publish/confirm actions
  - Secondary: Cancel/back actions
  - Draft: Save as draft actions
  - Danger: Delete/destructive actions

## Important Patterns
- Blog posts use portrait images with auto-generated thumbnails (300x300)
- All uploads go to `uploads/blog-posts/` directory
- CSRF protection enabled globally, exempt read-only endpoints
- Use `@login_required` decorator for authenticated routes
- Draft posts: Posts can be saved as drafts (is_draft=True) or published
  - Drafts visible only to authenticated users in blog listing
  - Public users cannot see draft posts
  - Use dual submit buttons: "Save as Draft" and "Publish"
  - Draft button uses duolingo-draft class, Publish uses duolingo-success
  - Edit form supports both save modes via different submit buttons

## Database Models
- User: Authentication with bcrypt password hashing
- BlogPost: title, content, portrait, thumbnail, dates, is_draft (Boolean)
- MinecraftCommand: RCON integration for game server

---

## 🤖 Agent-Powered Development Workflow

### Available Agents

**Meta-Orchestration:**
- `agent-organizer` - Master orchestrator for complex multi-step features
- `context-manager` - Maintains project state and knowledge across sessions

**Development:**
- `backend-architect` - Flask/Python architecture and design patterns
- `python-pro` - Advanced Python implementation and optimization
- `frontend-developer` - Jinja2 templates, jQuery, and UI implementation
- `flask-dev` - Project-specific Flask expertise (planning and analysis only)

**Quality Assurance:**
- `code-reviewer` - Pre-commit code quality and best practices review
- `architect-review` - Architecture consistency and design pattern validation
- `security-auditor` - Security review for auth, uploads, and data access

**Documentation:**
- `api-documenter` - API endpoint documentation and OpenAPI specs
- `documentation-expert` - Technical documentation and README updates

### Agent Usage Guidelines

**CRITICAL - flask-dev Agent:**
- ⚠️ **Use ONLY for planning and analysis, NEVER for direct file writes**
- Ask flask-dev to analyze code and create detailed plans
- Implement changes yourself using Edit/Write tools after reviewing flask-dev's plan
- This prevents agents from overwriting files incorrectly
- Example: "flask-dev, analyze routes_blogpost.py and create a plan for adding tags" → Then implement the plan yourself

**General Agent Best Practices:**
- Let `agent-organizer` coordinate complex tasks automatically
- Use `context-manager` to store/retrieve sprint context between sessions
- Invoke specific agents when you need domain expertise: "security-auditor, review upload logic"
- Always run `code-reviewer` before committing significant changes
- Use `architect-review` for blueprint structure or major architectural changes

---

## 📋 JIRA-Driven Development Workflow

### Step 1: Retrieve Task Instructions from Anytype

**Before starting any JIRA ticket**, search Anytype for task-specific instructions:

```
Search Anytype for "Claude Instruction" type with the ticket number:
- "TC-20 plan" → Sprint planning instructions
- "TC-47 MC sprint" → Minecraft feature sprint details
- "TC-4" → Specific ticket implementation guidance
```

**What to look for:**
- Acceptance criteria
- Technical constraints
- Design decisions
- Related tickets
- Special considerations

### Step 2: Initialize Task with Time Tracking

**At the START of work:**

```
Starting work on TC-XX at [get current time].

[If complex task] agent-organizer, analyze TC-XX requirements from 
Anytype instructions and create an implementation plan.

[If simple task] Implementing [brief description] for TC-XX.
```

**Claude Code will:**
1. Call `time:get_datetime` to record start time
2. If agent-organizer is invoked, it will:
   - Analyze codebase and Anytype instructions
   - Identify required agents (backend-architect, frontend-developer, etc.)
   - Create implementation plan with phases
   - Estimate complexity and token usage

### Step 3: Development Phase

**Let agents coordinate automatically:**

For complex features:
```
agent-organizer coordinates → backend-architect → frontend-developer → 
security-auditor → test-automator → code-reviewer
```

For focused changes:
```
"Use backend-architect to design the schema changes for TC-XX"
"Have security-auditor review the authentication logic"
"Get python-pro to optimize this database query"
```

**During development:**
- Agents work in isolated contexts
- context-manager tracks decisions and state
- You implement the actual code changes based on agent guidance
- Use flask-dev ONLY for analysis, not file modifications

### Step 4: Pre-Commit Review

**Before committing, ALWAYS:**

```
code-reviewer, analyze all changes for TC-XX and verify:
1. Security implications
2. Best practices adherence
3. No double-commits or logic errors
4. Proper error handling
5. CSRF protection where needed
```

**For architectural changes:**
```
architect-review, validate that TC-XX changes maintain consistency with:
1. Blueprint pattern
2. Separation of concerns
3. Database design patterns
```

### Step 5: Commit with Smart Commits

**When ready to commit:**

```
Ready to commit TC-XX. Current time is [get current time].
```

**Claude Code will:**
1. Call `time:get_datetime` to get end time
2. Calculate elapsed time (end - start)
3. Round to nearest 15 minutes (JIRA requirement)
4. Generate Smart Commit message

**Smart Commit Format:**
```bash
git commit -m "TC-XX #time [calculated]h [calculated]m #comment [detailed description]"

# Examples:
git commit -m "TC-4 #time 1h 30m #comment Added draft functionality with dual submit buttons and access controls"
git commit -m "TC-47 #time 2h 15m #comment Implemented Minecraft RCON integration with error handling"
git commit -m "TC-20 #time 45m #comment Updated sprint plan documentation in Anytype"
```

**If completing the ticket:**
```bash
git commit -m "TC-XX #time Xh Ym #comment [description] #close"
```

### Step 6: Update JIRA and Anytype

**After committing:**
1. Smart Commit automatically updates JIRA with time and comments
2. Update Anytype "Claude Instruction" if implementation differed from plan
3. Store any important decisions in context-manager:
   ```
   context-manager, store TC-XX implementation notes:
   - [Key decision 1]
   - [Technical approach used]
   - [Issues encountered and solutions]
   ```

### Step 7: Context Preservation

**End of session:**
```
context-manager, store current sprint state:
- Completed: TC-XX, TC-YY
- In progress: TC-ZZ (blocked on [reason])
- Next up: TC-AA
- Important notes: [any context for next session]
```

**Start of next session:**
```
context-manager, retrieve last sprint state and continue where we left off.
```

---

## 🔄 Example: Complete Ticket Workflow

### Simple Feature (TC-4: Draft Post Functionality)

```
# Step 1: Check Anytype for instructions
Search Anytype: "TC-4 draft" or "TC-4 Claude Instruction"

# Step 2: Initialize
Starting TC-4 at 2:00 PM. Implementing draft post functionality 
with dual submit buttons.

# Step 3: Let Claude work (with appropriate agents)
backend-architect designs is_draft field → python-pro implements logic →
frontend-developer adds UI controls → security-auditor reviews access

# Step 4: Review
code-reviewer, analyze TC-4 changes before commit.

# Step 5: Commit
Ready to commit TC-4. Current time is 3:45 PM.
→ Generates: "TC-4 #time 1h 45m #comment Implemented draft functionality 
with is_draft field, dual submit buttons, and draft visibility controls #close"

# Step 6: Store context
context-manager, store TC-4 implementation: Used dual submit pattern 
with name-based differentiation, added is_draft boolean to BlogPost model.
```

### Complex Feature (TC-47: Minecraft Sprint)

```
# Step 1: Check Anytype
Search Anytype: "TC-47 MC sprint" → Find sprint plan and requirements

# Step 2: Initialize with orchestration
Starting TC-47 at 10:00 AM. agent-organizer, analyze the MC sprint 
requirements from Anytype and coordinate implementation.

# Step 3: Agent orchestration (automatic)
agent-organizer analyzes → creates 5-phase plan →
backend-architect (RCON models) → python-pro (RCON client) →
frontend-developer (MC admin UI) → security-auditor (command validation) →
test-automator (integration tests) → code-reviewer (final review)

# Step 4: Review with multiple agents
code-reviewer, analyze all MC sprint changes.
security-auditor, specifically review RCON command validation and auth.

# Step 5: Commit
Ready to commit TC-47. Current time is 1:30 PM.
→ Generates: "TC-47 #time 3h 30m #comment Implemented complete Minecraft 
RCON integration with admin UI, command validation, and player management #close"

# Step 6: Document
Update Anytype "TC-47 MC sprint" with implementation notes.
context-manager, store TC-47: RCON uses mctools library, admin routes 
in routes_mc.py, validation in MinecraftCommand model.
```

---

## 🛠️ Common Development Tasks

### Starting a New Feature Branch
```bash
# Branch naming convention
git checkout -b enhancement/TC-XX-brief-description
git checkout -b bugfix/TC-XX-brief-description
git checkout -b styling/TC-XX-brief-description
```

### Database Migrations
```bash
# Development (activate venv first!)
source venv/bin/activate
python manage.py db migrate -m "Add field_name to Model"
python manage.py db upgrade

# Docker
docker-compose exec flask-site flask db migrate -m "Add field_name to Model"
docker-compose exec flask-site flask db upgrade

# Always include server_default for non-nullable columns
# Test rollback: flask db downgrade, then upgrade again
```

### Running the Application
```bash
# Development server (activate venv first!)
source venv/bin/activate
python run.py

# Production deploy
./grun.sh

# Docker development
docker-compose up --build

# Restart after model changes
docker-compose down && docker-compose up --build
```

### Running Tests
```bash
# Always activate virtual environment first
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_models.py::TestUser::test_user_creation -v
```

### Template Best Practices
- Cannot use Jinja2 syntax in HTML attribute values (e.g., `value="{{ ... }}"`)
- Use conditional blocks outside the element instead
- Always test forms after adding dual submit buttons
- Use duolingo button classes: `duolingo-primary`, `duolingo-success`, `duolingo-secondary`, `duolingo-draft`, `duolingo-danger`
- **Button elements**: Use `<button>` tags instead of `<a>` tags for better styling
  - For navigation: `<button type="button" onclick="window.location.href='{{ url_for(...) }}'">Text</button>`
  - For form submissions: `<button type="submit">Text</button>`
  - Avoid `<a href="..." class="duolingo-*">` as it renders with link styling instead of button styling

---

## 📊 Agent Coordination Patterns

### Pattern 1: Automatic Multi-Agent (Complex Features)
```
Starting TC-XX at [time]. agent-organizer, implement [complex feature] 
following Anytype instructions.

→ agent-organizer coordinates 4-6 agents automatically
→ Each agent works in isolated context
→ Results synthesized and reviewed
→ You implement based on coordinated plan
```

### Pattern 2: Sequential Single Agents (Focused Changes)
```
backend-architect, design schema for [feature].
→ Review design
python-pro, implement the schema changes.
→ Review implementation
security-auditor, review for access control issues.
→ Address any findings
code-reviewer, final review before commit.
```

### Pattern 3: Planning Only (Use flask-dev)
```
flask-dev, analyze routes_blogpost.py and create a detailed plan for 
adding tag functionality. DO NOT modify files.

→ Review flask-dev's plan
→ Implement changes yourself using Edit/Write tools
→ This prevents accidental file overwrites
```

### Pattern 4: Context Preservation (Between Sessions)
```
# End of day
context-manager, store sprint progress:
- Completed: TC-4, TC-16
- In progress: TC-47 (RCON client implemented, need UI)
- Blocked: TC-20 (waiting for design approval)
- Notes: RCON uses port 25575, tested with local server

# Next day
context-manager, what was the status of TC-47?
→ Retrieves: "In progress - RCON client implemented, need UI next"

Continue TC-47 at 9:00 AM. frontend-developer, create admin UI for 
Minecraft commands based on the RCON client from yesterday.
```

---

## 🔐 Security Checklist (Always Review)

Before committing any feature:
- [ ] `@login_required` on authenticated routes
- [ ] CSRF tokens in all forms
- [ ] File upload validation (secure_filename, file type checks)
- [ ] SQL injection prevention (always use SQLAlchemy ORM)
- [ ] XSS prevention (escape user content in templates)
- [ ] Environment variables for secrets (never hardcode)
- [ ] Access control (users can only access their own data)
- [ ] Error messages don't leak sensitive information

**Use security-auditor:**
```
security-auditor, review [feature] for common vulnerabilities:
- Authentication/authorization
- Input validation
- File upload security
- SQL injection vectors
- XSS risks
```

---

## 📝 Migration Best Practices

### Adding Non-Nullable Columns
```python
# ALWAYS include server_default for non-nullable fields
op.add_column('table_name', 
    sa.Column('new_field', sa.Boolean(), 
              nullable=False, 
              server_default='false'))
```

### Testing Migrations
```bash
# Always activate venv first
source venv/bin/activate

# Apply migration
flask db upgrade

# Verify
flask db current

# Test rollback
flask db downgrade
flask db upgrade

# Check for errors (Docker)
docker-compose logs -f flask-site
```

---

## 🎯 Quick Reference

### JIRA Smart Commit Format
```
TC-XX #time Xh Ym #comment Description [#close]
```

### Agent Invocation
```
# Let Claude choose
"Implement [feature]"

# Explicit agent
"Use [agent-name] to [task]"

# Orchestration
"agent-organizer, coordinate [complex task]"

# Context management
"context-manager, store/retrieve [information]"
```

### Time Tracking (Automatic)
```
1. Start: "Starting TC-XX at [time]"
2. Work: Agents coordinate or you implement
3. Commit: "Ready to commit TC-XX. Current time is [time]"
4. Result: Auto-calculated time in Smart Commit
```

### Anytype Integration
```
# Search for task instructions
Search: "TC-XX Claude Instruction"
Search: "TC-XX plan"
Search: "[sprint-name] Claude Instruction"

# Update after implementation
Store implementation notes in Anytype for future reference
```

---

## 🚀 Getting Started with a New Ticket

**Complete Workflow Template:**

```
# 1. Search Anytype for instructions
Search Anytype: "TC-XX" or "TC-XX Claude Instruction"

# 2. Create feature branch
git checkout -b enhancement/TC-XX-description

# 3. Start work with time tracking
Starting TC-XX at [current time]. [Brief description of task]

# 4. Use agent-organizer for complex tasks
agent-organizer, analyze TC-XX from Anytype instructions and coordinate implementation.

# OR use specific agents for focused tasks
backend-architect, design [specific component].

# 5. Implement based on agent guidance
[Make actual code changes using Edit/Write tools]

# 6. Pre-commit review
code-reviewer, analyze all changes for TC-XX.

# 7. Commit with auto time tracking
Ready to commit TC-XX. Current time is [current time].

# 8. Push and create PR (if needed)
git push origin enhancement/TC-XX-description

# 9. Store context for next session
context-manager, store TC-XX completion notes: [key decisions, approaches used]
```

---

## 📚 Additional Resources

- **JIRA Board**: turing-completely
- **Anytype**: Search "Claude Instruction" type for task details
- **Agent Documentation**: See `.claude/agents/` for individual agent capabilities
- **Docker Logs**: `docker-compose logs -f flask-site`
- **Database**: PostgreSQL via Docker, see `docker-compose.yml`

## Slash Commands
   - `/start-ticket` - Initialize ticket work
   - `/update-context` - Save progress
   - `/review-changes` - Multi-agent review
   - `/commit-ticket` - Commit with auto time
   - `/update-docs` - Update documentation