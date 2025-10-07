# App Directory Context

## Purpose
Main application package containing all Flask application logic, blueprints, models, forms, and filters. This is the core of the portfolio site.

## Key Files

### Application Factory & Initialization
- **__init__.py** - Application factory and extension initialization
  - `create_app()` → Flask app instance with all extensions configured
    - Inputs: None
    - Outputs: Configured Flask application
    - Side effects: Initializes database, CSRF, login manager, creates upload folders
  - Global extensions: `db`, `csrf`, `login_manager`, `migrate`, `rcon`
  - Registers 7 blueprints: main, auth, blogpost, mc, health, profile, admin
  - `load_user(user_id: int)` → User | None (Flask-Login callback)

### Data Models (models.py)
- **User** (UserMixin) - Authentication and user profiles
  - Fields: id, username, email, password_hash, profile_picture, bio, created_at
  - Methods:
    - `set_password(password: str)` → None (hashes and stores)
    - `check_password(password: str)` → bool (validates password)
    - `has_role(role_name: str)` → bool
    - `has_any_role(role_names: list[str])` → bool
  - Relationships: roles (many-to-many via role_assignments)

- **Role** - User permission roles
  - Fields: id, name, description, created_at
  - Relationship: assigned_users (backref from User.roles)

- **BlogPost** - Blog content with draft/publish states
  - Fields: id, title, content, portrait, thumbnail, created_at, updated_at, is_draft
  - Relationships: author_id → User

- **MinecraftCommand** - RCON command history
  - Fields: id, command, result, executed_at
  - Used by routes_mc.py for Minecraft server integration

### Forms (forms.py)
All forms use Flask-WTF with CSRF protection enabled:
- **ContactForm** - Contact page submission with custom PhoneNumber validator
- **BlogPostForm** - Dual submit buttons (save_draft, publish) for blog posts
- **ProfileEditForm** - User profile editing
- **RegistrationForm** - New user signup with password confirmation
- **LoginForm** - Username/password authentication
- Custom validator: `PhoneNumber()` - validates 10-digit US phone format

### Route Blueprints
- **routes.py** (`main_bp`) - Homepage, about, contact, portfolio
- **routes_auth.py** (`auth`) - Login, logout, registration
- **routes_blogpost.py** (`blogpost_bp`) - Blog CRUD, draft/publish toggle
- **routes_mc.py** (`mc_bp`) - Minecraft RCON integration
- **routes_health.py** (`health_bp`) - Health check endpoint (CSRF exempt)
- **routes_profile.py** (`profile_bp`) - User profile viewing/editing
- **routes_admin.py** (`admin_bp`) - Admin panel with role management

### Utilities
- **filters.py** - Jinja2 template filters
  - `register_filters(app)` → None
  - Custom filters for timezone conversions, date formatting

- **auth_decorators.py** - Custom authorization decorators
  - `@role_required(role_name)` - Requires specific role
  - `@admin_required` - Shortcut for admin role
  - Works with User.has_role() for access control

## Database Patterns
1. **ORM Only**: Always use SQLAlchemy, never raw SQL
2. **Timezone-aware**: Use `datetime.now(timezone.utc)` for timestamps
3. **Password Security**: Use werkzeug's `generate_password_hash` / `check_password_hash`
4. **Relationships**: Leverage SQLAlchemy relationships, not manual joins
5. **Migrations**: Any model changes require `flask db migrate` + `flask db upgrade`

## Security Patterns
1. **CSRF**: Enabled globally via CSRFProtect, exempt only read-only endpoints
2. **Authentication**: Use `@login_required` from flask_login
3. **Authorization**: Use custom decorators from auth_decorators.py
4. **Password Handling**: Never store plaintext, always use password_hash
5. **File Uploads**: Validate extensions with FileAllowed validator
6. **Role-Based Access**: Use has_role() / has_any_role() for permission checks

## Blueprint Registration Pattern
```python
# 1. Create blueprint in routes_*.py
from flask import Blueprint
new_bp = Blueprint('new_bp', __name__)

# 2. Define routes
@new_bp.route('/path')
def handler():
    pass

# 3. Register in __init__.py create_app()
from app.routes_new import new_bp
app.register_blueprint(new_bp)
```

## Form Patterns
1. **Dual Submit Buttons**: Use separate SubmitField for different actions (save_draft vs publish)
2. **Custom Validators**: Create validator classes with `__call__(form, field)` method
3. **File Uploads**: Use `FileField` with `FileAllowed` validator
4. **CSRF**: Automatically included in forms, render with `{{ form.csrf_token }}`

## Agent Touchpoints

### backend-architect
- Needs: Blueprint structure, model relationships, database schema
- Common tasks: Designing new models, planning API endpoints, schema migrations
- Key files: models.py, __init__.py, new routes_*.py blueprints

### python-pro
- Needs: ORM patterns, form validators, authentication logic
- Common tasks: Optimizing queries, implementing custom validators, refactoring
- Key files: models.py, forms.py, auth_decorators.py

### flask-dev (PLANNING ONLY)
- Needs: Full understanding of blueprint registration, model structure
- Common tasks: Creating implementation plans for new features
- **CRITICAL**: Never directly modifies files, only provides analysis

### security-auditor
- Needs: Authentication flow, CSRF implementation, password handling
- Common tasks: Auditing @login_required usage, validating file uploads, reviewing role checks
- Key files: routes_auth.py, auth_decorators.py, __init__.py (CSRF config)

### frontend-developer
- Needs: Form definitions, template context variables
- Common tasks: Creating forms, understanding what data routes pass to templates
- Key files: forms.py, routes_*.py (for context variables)

## Common Tasks

### Adding a New Model
1. Define class in models.py inheriting from db.Model
2. Add fields with db.Column()
3. Run `flask db migrate -m "Description"`
4. Run `flask db upgrade`
5. Test rollback: `flask db downgrade` then `flask db upgrade`

### Creating a New Blueprint
1. Create `app/routes_feature.py`
2. Define blueprint: `feature_bp = Blueprint('feature', __name__)`
3. Add routes with decorators: `@feature_bp.route('/path')`
4. Import and register in `__init__.py` create_app()
5. Add CSRF exemption if read-only: `csrf.exempt(feature_bp)`

### Adding a New Form
1. Create form class in forms.py inheriting FlaskForm
2. Define fields with validators
3. Add submit button(s)
4. Render in template with `{{ form.hidden_tag() }}`
5. Process in route with `form.validate_on_submit()`

### Implementing Role-Based Access
1. Create role in database via seed_roles.py or admin panel
2. Assign role to user: `user.roles.append(role)`
3. Use decorator: `@role_required('role_name')`
4. Or check manually: `current_user.has_role('role_name')`

## Related Directories
- `/templates/` - Jinja2 HTML templates rendered by routes
- `/static/` - CSS, JavaScript, images served by Flask
- `/migrations/` - Database migration files (auto-generated)
- `/uploads/` - User-uploaded files (blog-posts, profiles)

## File Upload Pattern
```python
# In route
file = request.files.get('file')
if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
```

## Version
Current: 0.2.2 (defined in __init__.py)
