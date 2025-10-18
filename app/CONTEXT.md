# App Directory Context

## Purpose
Main application package containing a modular Flask application architecture with separated components for models, forms, routes, and utilities.

## Modular Structure Overview
- **models/**: Database models organized by domain
  - `__init__.py`: Centralized model exports
  - `user.py`: User and Role models
  - `blog.py`: BlogPost model
  - `minecraft.py`: MinecraftCommand model

- **forms/**: Form definitions
  - `__init__.py`: Centralized form exports
  - `contact.py`: Contact submission form
  - `blog.py`: Blog post forms
  - `profile.py`: User profile and settings forms
  - `admin.py`: Administrative forms

- **routes/**: Route blueprints
  - `__init__.py`: Centralized route exports
  - `main.py`: Core application routes
  - `auth.py`: Authentication routes
  - `blogpost.py`: Blog management routes
  - `mc.py`: Minecraft server integration routes
  - `health.py`: Health check routes
  - `profile.py`: User profile management
  - `admin.py`: Admin panel routes

- **utils/**: Utility modules
  - `__init__.py`: Centralized utility exports
  - `auth_decorators.py`: Role-based access decorators
  - `filters.py`: Jinja2 template filters
  - `file_validation.py`: File upload validation
  - `image_utils.py`: Image processing utilities

## Key Changes from Previous Architecture

### Improvements
- **Separation of Concerns**: Each module now has a single, focused responsibility
- **Easier Navigation**: Logically grouped files make finding code simpler
- **Scalability**: Easier to add new features without modifying existing files
- **Maintainability**: Smaller, more focused files are easier to understand and modify

### Import Patterns
```python
# Models
from app.models import User, BlogPost, Role

# Forms
from app.forms import ContactForm, BlogPostForm

# Routes
from app.routes import main, auth, blogpost

# Utilities
from app.utils import (
    require_role,
    require_any_role,
    register_filters,
    validate_image_file
)
```

## Application Factory (__init__.py)
- Configures Flask application with all extensions
- Registers blueprints from modular route files
- Maintains consistent initialization and configuration

### Blueprint Registration
```python
def create_app():
    # Initialize app and extensions
    app = Flask(__name__)

    # Register blueprints from modular routes
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(blogpost)
    app.register_blueprint(mc)
    app.register_blueprint(health)
    app.register_blueprint(profile)
    app.register_blueprint(admin)
```

## Database Models
### User Model (`models/user.py`)
- Authentication and user profile management
- Role-based access control
- Methods: `set_password()`, `check_password()`, `has_role()`

### BlogPost Model (`models/blog.py`)
- Blog content management
- Draft/publish state support
- Relationships with User model

### MinecraftCommand Model (`models/minecraft.py`)
- RCON command tracking
- Server interaction logging

## Forms
### Design Principles
- Use Flask-WTF with CSRF protection
- Modular form definitions
- Custom validators
- Dual submit buttons for complex interactions

## Routes
### Blueprint Pattern
- Each route file represents a specific domain
- Consistent naming and structure
- Centralized in `routes/` directory
- Leverages Flask's blueprint mechanism

## Utilities
### Key Components
- Authentication decorators
- Jinja2 template filters
- File validation
- Image processing utilities

## Security Patterns
1. **Authentication**: `@login_required` on protected routes
2. **Authorization**: Role-based access via custom decorators
3. **Input Validation**: Comprehensive form and file validation
4. **CSRF Protection**: Enabled globally with exemptions for read-only routes

## Agent Touchpoints

### backend-architect
- Analyze new modular architecture
- Plan blueprint expansions
- Design model relationships
- Recommend optimization strategies

### python-pro
- Implement complex logic in utility modules
- Optimize database queries
- Develop custom validators and decorators

### flask-dev (PLANNING ONLY)
- Analyze current architecture
- Propose modularization improvements
- Create implementation plans

### security-auditor
- Review authentication flows
- Validate access control mechanisms
- Assess file upload and input validation

### frontend-developer
- Understand new form and route structures
- Create templates compatible with modular architecture
- Leverage centralized context variables

## Version
Current: 0.2.4 (reflects architectural refactoring)