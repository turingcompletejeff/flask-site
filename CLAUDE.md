# Flask Portfolio Site - Project Context

## Architecture
- Flask web framework with Blueprint architecture
- PostgreSQL database via SQLAlchemy ORM
- Gunicorn WSGI server for production
- Docker containerization with Portainer orchestration

## Coding Conventions
- Follow PEP 8 for Python code
- Use Blueprint pattern for route organization
- Always use environment variables for secrets (never hardcode)
- Database migrations: Use Flask-Migrate (flask db migrate/upgrade)
- Button styling: Use duolingo-buttons.css classes consistently

## Important Patterns
- Blog posts use portrait images with auto-generated thumbnails (300x300)
- All uploads go to `uploads/blog-posts/` directory
- CSRF protection enabled globally, exempt read-only endpoints
- Use `@login_required` decorator for authenticated routes

## Database Models
- User: Authentication with bcrypt password hashing
- BlogPost: title, content, portrait, thumbnail, dates
- MinecraftCommand: RCON integration for game server

## JIRA Integration
- Use Smart Commits: "TC-XX #time Xh #comment Message"
- Branch naming: feature/TC-XX-description
- Always include time tracking rounded to 15min

## Common Tasks
- Start dev server: `python run.py`
- Production deploy: `./grun.sh`
- Docker dev: `docker-compose up --build`
- Run migration: `docker-compose exec flask-site flask db migrate -m "message"`
- Apply migration: `docker-compose exec flask-site flask db upgrade`

## Development Best Practices

### Using Agents
- **flask-dev agent**: Use for PLANNING and analysis, not direct file writes
  - Ask flask-dev to analyze and create detailed plans
  - Then implement changes yourself using Edit/Write tools
  - This prevents agents from overwriting files incorrectly
- **code-reviewer agent**: Always run before committing significant changes
  - Reviews for security, logic errors, and best practices
  - Can catch issues like missing access controls or double-commits

### Migration Best Practices
- Always include `server_default` when adding non-nullable columns
- Test migrations with `docker-compose exec` before committing
- Use `flask db downgrade` and `flask db upgrade` to test rollback
- Check migration with `flask db current` to verify application

### Template Best Practices
- Cannot use Jinja2 syntax in HTML attribute values (e.g., `value="{{ ... }}"`)
- Use conditional blocks outside the element instead
- Always test forms after adding dual submit buttons
- Use duolingo button classes: `duolingo-primary`, `duolingo-success`, `duolingo-secondary`, `duolingo-draft`, `duolingo-danger`

### Docker Development
- Restart containers after model changes: `docker-compose down && docker-compose up --build`
- Migrations persist in Docker volumes
- Check logs: `docker-compose logs -f flask-site`