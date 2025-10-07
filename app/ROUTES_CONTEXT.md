# Routes Context

## Purpose
Blueprint modules defining all HTTP endpoints and request handlers. Each routes_*.py file is a self-contained feature blueprint.

## Blueprint Architecture Pattern
Each blueprint follows this structure:
```python
from flask import Blueprint
feature_bp = Blueprint('feature_bp', __name__)

@feature_bp.route('/path')
@decorators  # login_required, role_required, etc.
def handler():
    # Route logic
    pass
```

## Route Files Overview

### routes.py (main_bp)
**Public-facing pages and core functionality**

#### Routes:
- `GET /` - Homepage with blog post listing
  - Inputs: None (optional flash message query params)
  - Outputs: Renders index.html with blog_posts context
  - Logic: Shows drafts to authenticated users, only published to public

- `GET /about` - About page
  - Inputs: None
  - Outputs: Renders about.html

- `GET|POST /contact` - Contact form submission
  - Inputs: ContactForm (name, email, phone, reason, message)
  - Outputs: JSON response for AJAX, redirect for standard forms
  - Side effects: Sends email via SMTP to ADMIN_EMAIL
  - Security: Form validation, email sanitization

- `GET /uploads/blog-posts/<filename>` - Serve uploaded blog images
  - Inputs: filename (string)
  - Outputs: File from BLOG_POST_UPLOAD_FOLDER
  - Security: Uses send_from_directory (prevents path traversal)

#### Helper Functions:
- `formatContactEmail(form)` → EmailMessage object
- `sendAnEmail(message)` → None (SMTP send with error handling)

### routes_auth.py (auth)
**Authentication: login, logout, registration**

#### Routes:
- `GET|POST /login` - User login
  - Inputs: username, password (form)
  - Outputs: Redirect to index on success, re-render form on failure
  - Side effects: Creates user session via login_user()
  - Security: Password checked via User.check_password()

- `GET|POST /register` - New user registration
  - Inputs: username, email, password (form)
  - Outputs: Redirect to login on success
  - Side effects: Creates new User in database
  - Security: Checks REGISTRATION_ENABLED config, validates unique username

- `GET /logout` - User logout
  - Decorator: @login_required
  - Inputs: None
  - Outputs: Redirect to index
  - Side effects: Destroys user session via logout_user()

### routes_blogpost.py (blogpost_bp)
**Blog post CRUD with draft/publish workflow**

#### Routes:
- `GET /post/<int:post_id>` - View single blog post
  - Inputs: post_id (URL parameter)
  - Outputs: Renders view_post.html with post context
  - Security: Drafts hidden from unauthenticated users (404)

- `GET|POST /post/new` - Create new blog post
  - Decorator: @login_required, @require_any_role(['blogger', 'admin'])
  - Inputs: BlogPostForm (title, content, portrait, thumbnail, save_draft/publish)
  - Outputs: Redirect to view_post on success
  - Side effects: Saves files to BLOG_POST_UPLOAD_FOLDER, creates BlogPost record
  - Security: Image validation (magic numbers), filename sanitization, file size limits
  - Image Processing: Auto-generates 300x300 thumbnail if not provided

- `GET|POST /post/<int:post_id>/edit` - Edit existing blog post
  - Decorator: @login_required, @require_any_role(['blogger', 'admin'])
  - Inputs: post_id, BlogPostForm
  - Outputs: Redirect to view_post on success
  - Side effects: Updates BlogPost record, handles image replacements
  - Security: Same validation as new_post

- `POST /post/<int:post_id>/delete` - Delete blog post
  - Decorator: @login_required, @require_any_role(['blogger', 'admin'])
  - Inputs: post_id
  - Outputs: Redirect to index
  - Side effects: Deletes BlogPost record, removes image files

- `POST /post/<int:post_id>/toggle-draft` - Toggle draft/published status
  - Decorator: @login_required, @require_any_role(['blogger', 'admin'])
  - Inputs: post_id
  - Outputs: JSON response
  - Side effects: Flips is_draft boolean

#### Helper Functions:
- `validate_image_file(file)` → (bool, error_msg) - Validates file type, size, magic numbers
- `sanitize_filename(filename)` → str - Removes special characters

### routes_mc.py (mc_bp)
**Minecraft server RCON integration**

#### Routes:
- RCON command execution endpoints
- Player management (whitelist, op, kick, ban)
- Server status queries

#### Security:
- @login_required on all routes
- @require_any_role(['admin']) for destructive commands
- RCON password from environment variables

### routes_health.py (health_bp)
**Health check endpoint for monitoring**

#### Routes:
- `GET /health` - Application health status
  - Inputs: None
  - Outputs: JSON with status and timestamp
  - Security: CSRF exempt (read-only, no auth required)

### routes_profile.py (profile_bp)
**User profile viewing and editing**

#### Routes:
- `GET /profile/<username>` - View user profile
  - Inputs: username (URL parameter)
  - Outputs: Renders profile.html with user data

- `GET|POST /profile/edit` - Edit current user profile
  - Decorator: @login_required
  - Inputs: ProfileEditForm (bio, profile_picture)
  - Outputs: Redirect to profile view on success
  - Side effects: Updates User record, handles profile picture upload
  - Security: Image validation, user can only edit own profile

### routes_admin.py (admin_bp)
**Admin panel and role management**

#### Routes:
- Admin dashboard
- User management (view users, assign roles)
- Role management (create, edit, delete roles)

#### Security:
- All routes require @admin_required decorator
- Role assignment validation
- Audit logging for admin actions

## Common Route Patterns

### Form Handling Pattern
```python
form = SomeForm()
if form.validate_on_submit():
    # Process form data
    # Save to database
    flash('Success message', 'success')
    return redirect(url_for('blueprint.route'))
return render_template('template.html', form=form)
```

### Dual Submit Button Pattern (Draft/Publish)
```python
if form.validate_on_submit():
    is_draft = bool(form.save_draft.data)  # True if "Save Draft" clicked
    obj.is_draft = is_draft
    db.session.commit()
```

### File Upload Pattern
```python
file = form.file_field.data
if file:
    # 1. Validate
    is_valid, error = validate_image_file(file)
    # 2. Sanitize filename
    safe_name = secure_filename(sanitize_filename(file.filename))
    # 3. Save
    file.save(os.path.join(UPLOAD_FOLDER, safe_name))
```

### AJAX Response Pattern
```python
if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return jsonify({'success': True, 'message': 'Done'})
else:
    flash('Done', 'success')
    return redirect(url_for('route'))
```

## Security Patterns

### Authentication Decorators
- `@login_required` - Requires authenticated user
- `@require_any_role(['role1', 'role2'])` - Requires at least one role
- `@admin_required` - Shortcut for admin role

### File Upload Security
1. **Validate file type**: Check magic numbers, not just extension
2. **Sanitize filename**: Remove special characters, use secure_filename()
3. **Limit file size**: Enforced by MAX_CONTENT_LENGTH in config
4. **Save securely**: Use send_from_directory for serving

### CSRF Protection
- Enabled globally for all POST/PUT/DELETE
- Exempt read-only endpoints: health_bp
- Forms automatically include CSRF token

### Draft Post Security
- Unauthenticated users cannot view drafts
- Only bloggers/admins can create/edit posts
- Draft status changes logged

## Agent Touchpoints

### backend-architect
- Needs: Blueprint structure, route patterns, security decorators
- Common tasks: Designing new endpoints, planning API structure
- Key files: All routes_*.py, auth_decorators.py

### python-pro
- Needs: Form handling patterns, file upload logic, database queries
- Common tasks: Optimizing queries, refactoring handlers, error handling
- Key files: routes_blogpost.py (complex file handling), routes_mc.py (RCON)

### security-auditor
- Needs: Authentication flow, file upload validation, CSRF implementation
- Common tasks: Auditing upload handlers, validating access control, reviewing auth
- Key files: routes_auth.py, routes_blogpost.py, auth_decorators.py

### frontend-developer
- Needs: Route context variables, form fields, AJAX endpoints
- Common tasks: Understanding what data templates receive, AJAX integration
- Key files: All routes_*.py for render_template() calls

### flask-dev (PLANNING ONLY)
- Needs: Complete blueprint architecture, registration pattern
- Common tasks: Planning new blueprints, analyzing route dependencies
- **CRITICAL**: Never modifies routes directly

## Common Tasks

### Adding a New Route to Existing Blueprint
```python
@blueprint_bp.route('/new-path', methods=['GET', 'POST'])
@login_required  # if auth required
def new_handler():
    # Implementation
    return render_template('template.html')
```

### Creating a New Blueprint
1. Create `app/routes_feature.py`
2. Define blueprint: `feature_bp = Blueprint('feature', __name__)`
3. Add routes with decorators
4. Import in `app/__init__.py`: `from app.routes_feature import feature_bp`
5. Register: `app.register_blueprint(feature_bp)`
6. Exempt from CSRF if read-only: `csrf.exempt(feature_bp)`

### Adding Role-Based Access
```python
from app.auth_decorators import require_any_role

@route_bp.route('/protected')
@login_required
@require_any_role(['admin', 'moderator'])
def protected_route():
    pass
```

### Handling File Uploads
```python
from app.utils.file_validation import validate_image_file, sanitize_filename
from werkzeug.utils import secure_filename

file = form.file.data
if file:
    is_valid, error = validate_image_file(file)
    if not is_valid:
        flash(error, 'danger')
        return redirect(...)

    filename = secure_filename(sanitize_filename(file.filename))
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
```

## Related Directories
- `app/templates/` - Jinja2 templates rendered by routes
- `app/forms.py` - WTForms used by routes
- `app/models.py` - Database models queried by routes
- `app/auth_decorators.py` - Custom authorization decorators
- `uploads/` - Files uploaded via routes

## Error Handling Pattern
```python
try:
    # Operation
    db.session.commit()
    flash('Success', 'success')
except Exception as e:
    db.session.rollback()
    current_app.logger.error(f'Error: {e}')
    flash('Error occurred', 'danger')
```

## Logging Pattern
```python
current_app.logger.info(f'User {current_user.id} performed action')
current_app.logger.warning(f'Validation failed: {error}')
current_app.logger.error(f'Critical error: {exception}')
```
