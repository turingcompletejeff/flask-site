# Root Directory Context

## Purpose
Project root containing configuration, deployment scripts, and entry points for the Flask portfolio site.

## Key Files

### Application Entry Points
- **run.py** - Development server entry point
  - `create_app()` → Flask app instance
  - Runs on `0.0.0.0:8000` for local testing

- **config.py** - Centralized configuration class
  - `Config` class with environment-based settings
  - Database connection pooling with timeout protection
  - Upload folder paths (blog-posts, profiles)
  - Security: 5MB upload limit, CSRF protection
  - RCON settings for Minecraft server integration
  - Email/SMTP configuration

### Deployment & Infrastructure
- **Dockerfile** - Container image definition for production
- **docker-compose.yml** - Local development container orchestration
- **portainer-stack.yml** - Production stack configuration for Portainer

### Database & Setup
- **db-init/seed_roles.py** - Database seeding script for initial roles/data (UPDATED LOCATION)
- **requirements.txt** - Python package dependencies (pip install -r)

### Documentation
- **README.md** - Project overview and setup instructions
- **CLAUDE.md** - AI agent coordination and development workflow guide
- **LICENSE** - Project licensing information

## Environment Variables (from config.py)
Required in `.env` file:
- `DATABASE_TYPE`, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- `SECRET_KEY` - Flask session security
- `RCON_PASS`, `MC_HOST`, `MC_PORT` - Minecraft RCON integration
- `REGISTRATION_ENABLED` - Toggle user registration (default: True)
- `MAIL_USER`, `MAIL_PW` - SMTP credentials for email

## Patterns to Follow
1. **Configuration**: Always use `os.environ.get()` for secrets/config
2. **Database**: Use connection pooling with `pool_pre_ping=True` for reliability
3. **Security**: Never hardcode credentials; use environment variables
4. **Deployment**: Use Docker for production, run.py for local dev

## Agent Touchpoints (Unchanged)
[Previous agent touchpoints remain the same]

## Common Tasks
1. **Adding new environment variable**: Update `config.py` Config class, document in README.md
2. **Modifying database settings**: Edit Config.SQLALCHEMY_* properties
3. **Changing upload limits**: Modify Config.MAX_CONTENT_LENGTH
4. **Adding Python dependency**: Update requirements.txt, rebuild Docker image
5. **Deployment**: Use `./run.py` for development, Docker for production (UPDATED FROM grun.sh)

## Related Directories
- `app/` - Main application code with new modular structure
  - `models/` - Separate model files for each domain
  - `forms/` - Modular form definitions
  - `routes/` - Modular route blueprints
  - `utils/` - Centralized utility modules
- `migrations/` - Database migration files
- `uploads/` - User-uploaded files (blog-posts, profiles)
- `.claude/` - Agent definitions and slash commands
- `db-init/` - Database initialization scripts

## Modular Architecture Overview
The project has been refactored to use a more modular architecture:
- Separate directories for models, forms, routes, and utilities
- Each directory includes an `__init__.py` for centralized exports
- Improved separation of concerns
- More maintainable and scalable code structure

### Import Patterns
```python
# Models - Import from centralized location
from app.models import User, BlogPost, Role

# Forms
from app.forms import ContactForm, BlogPostForm

# Routes
from app.routes import main, auth, blogpost

# Utilities
from app.utils import require_role, register_filters
```

## Version
Current: 0.2.4 (defined in app/__init__.py)