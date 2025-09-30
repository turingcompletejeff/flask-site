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
- Database migrations NOT currently used (manual schema changes)

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