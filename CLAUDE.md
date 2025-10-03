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
- **Button elements**: Use `<button>` tags instead of `<a>` tags for better styling
  - For navigation: `<button type="button" onclick="window.location.href='{{ url_for(...) }}'">Text</button>`
  - For form submissions: `<button type="submit">Text</button>`
  - Avoid `<a href="..." class="duolingo-*">` as it renders with link styling instead of button styling

### Docker Development
- Restart containers after model changes: `docker-compose down && docker-compose up --build`
- Migrations persist in Docker volumes
- Check logs: `docker-compose logs -f flask-site`