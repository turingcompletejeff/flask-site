# Security Patterns & Standards

## Overview
Comprehensive security guide for the Flask portfolio application. This document defines security patterns, authentication/authorization standards, and common vulnerability prevention strategies.

## Authentication

### Password Security

#### Password Hashing
**Always use bcrypt for password hashing.**

```python
from app.models import User

# Setting password (automatic bcrypt hashing)
user = User(username='john', email='john@example.com')
user.set_password('secure_password_123')  # ✓ Hashed with bcrypt

# Verifying password
if user.check_password('user_input_password'):
    # Password is correct
    login_user(user)
```

**Security Requirements:**
- ✅ Use `user.set_password()` method (never set `password_hash` directly)
- ✅ Bcrypt automatically salts passwords (unique salt per password)
- ✅ Passwords stored as bcrypt hashes (`$2b$...`)
- ❌ Never store plaintext passwords
- ❌ Never log or display `password_hash`

#### Password Validation
```python
# In forms.py
from wtforms.validators import Length, Regexp

class RegistrationForm(FlaskForm):
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters'),
        # Optional: Add complexity requirements
        # Regexp(r'^(?=.*[A-Za-z])(?=.*\d)', message='Password must contain letters and numbers')
    ])
```

**Best Practices:**
- Minimum 8 characters
- Consider complexity requirements (letters, numbers, symbols)
- Provide clear error messages
- Never reveal if username or password is wrong (use generic "Invalid credentials")

### Session Management

#### Flask-Login Configuration
```python
# In app/__init__.py
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Redirect to login
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

#### Session Security
```python
# In config.py
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Required for session security
    SESSION_COOKIE_SECURE = True  # HTTPS only (production)
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
```

**Security Checklist:**
- ✅ Strong SECRET_KEY (environment variable, never hardcoded)
- ✅ HTTPS-only cookies in production
- ✅ HttpOnly flag prevents XSS session theft
- ✅ SameSite prevents CSRF attacks
- ✅ Session timeout (24 hours default)

## Authorization

### Role-Based Access Control (RBAC)

#### Decorator: `@login_required`
Require authentication (any logged-in user).

```python
from flask_login import login_required

@blogpost_bp.route('/post/new', methods=['GET', 'POST'])
@login_required  # ✓ Must be logged in
def new_post():
    # Only authenticated users can access
    pass
```

#### Decorator: `@require_role(role_name)`
Require specific role(s).

```python
from app.utils.decorators import require_role

@admin_bp.route('/admin')
@login_required
@require_role('admin')  # ✓ Must have admin role
def admin_dashboard():
    # Only users with admin role can access
    pass
```

**Multi-Role Support:**
```python
@require_role(['admin', 'blogger'])  # Either admin OR blogger
def content_management():
    pass
```

#### Manual Role Checks
```python
from flask_login import current_user

# Check single role
if current_user.has_role('admin'):
    # Admin-only logic
    pass

# Check multiple roles (any)
if current_user.has_any_role(['admin', 'blogger']):
    # Admin or blogger logic
    pass

# Check if user is admin
if current_user.is_admin():
    # Shorthand for has_role('admin')
    pass
```

#### Template-Based Authorization
```jinja2
{# Show admin link only to admins #}
{% if current_user.has_role('admin') %}
  <a href="{{ url_for('admin.admin_dashboard') }}">Admin Panel</a>
{% endif %}

{# Show edit button to blogger or admin #}
{% if current_user.has_any_role(['blogger', 'admin']) %}
  <a href="{{ url_for('blogpost.edit_post', post_id=post.id) }}">Edit</a>
{% endif %}
```

### Access Control Patterns

#### Resource Ownership Validation
```python
@blogpost_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    # ✓ Check ownership or admin status
    if not (current_user.is_admin() or post.author_id == current_user.id):
        abort(403)  # Forbidden

    # Proceed with edit
```

#### Draft Post Access Control
```python
@blogpost_bp.route('/post/<int:post_id>')
def view_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    # ✓ Draft posts only visible to authenticated users
    if post.is_draft and not current_user.is_authenticated:
        abort(404)  # Pretend it doesn't exist

    return render_template('view_post.html', post=post)
```

## CSRF Protection

### Global CSRF Protection
```python
# In app/__init__.py
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
csrf.init_app(app)

# Exempt health check endpoint
csrf.exempt(health_bp)
```

### Form CSRF Tokens
**All forms MUST include CSRF token.**

```html
<form method="POST" action="/login">
  {{ form.hidden_tag() }}  <!-- ✓ Includes CSRF token -->

  {{ form.username.label }}
  {{ form.username }}

  {{ form.submit() }}
</form>
```

**Manual CSRF Token (non-WTForms):**
```html
<form method="POST">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
  <!-- Other fields -->
</form>
```

### AJAX CSRF Protection
```javascript
// In layout.html - Global CSRF setup
<meta name="csrf-token" content="{{ csrf_token() }}">

<script>
// Automatically add CSRF token to all AJAX requests
$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
      var csrfToken = $("meta[name=csrf-token]").attr("content");
      xhr.setRequestHeader("X-CSRFToken", csrfToken);
    }
  }
});
</script>
```

**Manual AJAX CSRF:**
```javascript
// Get token from meta tag
let csrfToken = $("meta[name=csrf-token]").attr("content");

// Add to POST request
$.ajax({
  url: '/some/route',
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken
  },
  data: { /* data */ }
});
```

### CSRF Testing
```python
# Test with CSRF disabled (default)
def test_login(client, regular_user):
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 302

# Test with CSRF enabled
def test_csrf_protection(csrf_client):
    # Missing token should fail
    response = csrf_client.post('/login', data={
        'username': 'test',
        'password': 'test'
    })
    assert response.status_code == 400
```

## Input Validation & Sanitization

### SQL Injection Prevention
**Always use SQLAlchemy ORM (never raw SQL with user input).**

```python
# ✅ SAFE - Parameterized via ORM
username = request.form.get('username')
user = User.query.filter_by(username=username).first()

# ✅ SAFE - Using ORM methods
users = User.query.filter(User.email.like(f'%{search_term}%')).all()

# ❌ DANGEROUS - Raw SQL with user input
query = f"SELECT * FROM users WHERE username = '{username}'"  # SQL INJECTION!
db.session.execute(query)
```

**If raw SQL is absolutely necessary:**
```python
# Use parameterized queries
from sqlalchemy import text

username = request.form.get('username')
query = text("SELECT * FROM users WHERE username = :username")
result = db.session.execute(query, {'username': username})
```

### XSS (Cross-Site Scripting) Prevention

#### Jinja2 Auto-Escaping
Jinja2 auto-escapes by default. **Trust this behavior.**

```jinja2
{# ✓ SAFE - Auto-escaped #}
<p>{{ user.bio }}</p>

{# ❌ DANGEROUS - Disables escaping, use ONLY for trusted HTML #}
<p>{{ user.bio|safe }}</p>
```

**When to use `|safe`:**
- ✅ Admin-created content (after sanitization)
- ✅ Markdown-rendered content (after sanitization)
- ❌ NEVER on direct user input
- ❌ NEVER on URL parameters
- ❌ NEVER on form data

#### HTML Sanitization
```python
# For user-generated HTML content
import bleach

ALLOWED_TAGS = ['p', 'strong', 'em', 'a', 'ul', 'ol', 'li']
ALLOWED_ATTRS = {'a': ['href', 'title']}

user_html = request.form.get('content')
clean_html = bleach.clean(user_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
```

### File Upload Security

#### Secure Filename
**Always use `secure_filename()` to prevent directory traversal.**

```python
from werkzeug.utils import secure_filename

file = request.files.get('portrait')
if file:
    filename = secure_filename(file.filename)  # ✓ Prevents "../../../etc/passwd"
    filepath = os.path.join(app.config['BLOG_POST_UPLOAD_FOLDER'], filename)
    file.save(filepath)
```

#### File Type Validation
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# In route
file = request.files.get('portrait')
if file and allowed_file(file.filename):
    # ✓ Process file
    pass
else:
    flash('Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP', 'danger')
```

#### File Size Limits
```python
# In config.py
class Config:
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit

# In route (optional additional check)
if file.content_length > app.config['MAX_CONTENT_LENGTH']:
    flash('File too large. Maximum size: 5 MB', 'danger')
    return redirect(request.url)
```

#### Image Validation (Verify actual image)
```python
from PIL import Image

file = request.files.get('portrait')
try:
    img = Image.open(file.stream)
    img.verify()  # ✓ Verify it's actually an image
except Exception:
    flash('Invalid image file', 'danger')
    return redirect(request.url)
```

#### Complete Upload Security Pattern
```python
from werkzeug.utils import secure_filename
from PIL import Image
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def secure_upload(file, upload_folder):
    """Securely handle file upload with validation."""
    # Check file exists
    if not file or not file.filename:
        return None, 'No file provided'

    # Check extension
    if not allowed_file(file.filename):
        return None, 'Invalid file type'

    # Secure filename
    filename = secure_filename(file.filename)

    # Verify it's an actual image
    try:
        img = Image.open(file.stream)
        img.verify()
    except Exception:
        return None, 'Invalid image file'

    # Reset stream after verify
    file.stream.seek(0)

    # Save file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return filename, None
```

## Environment Variables & Secrets

### Secret Management
**Never hardcode secrets in code.**

```python
# ✅ CORRECT - Use environment variables
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    RCON_PASSWORD = os.environ.get('RCON_PASSWORD')

# ❌ WRONG - Hardcoded secrets
class Config:
    SECRET_KEY = 'super-secret-key-123'  # NEVER DO THIS
```

### .env File (Development Only)
```bash
# .env (NEVER commit to git)
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/db
RCON_PASSWORD=rcon-password
```

**Add to .gitignore:**
```
.env
*.env
.env.*
```

### Production Secrets
- Use environment variables in production
- Consider secret management services (AWS Secrets Manager, HashiCorp Vault)
- Never log secrets
- Rotate secrets regularly

## Error Handling

### Don't Leak Information
```python
# ✅ GOOD - Generic error message
try:
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        flash('Invalid username or password', 'danger')  # Generic
except Exception as e:
    app.logger.error(f'Login error: {e}')
    flash('An error occurred. Please try again.', 'danger')

# ❌ BAD - Reveals user existence
if not user:
    flash('Username not found', 'danger')  # Leaks info
elif not user.check_password(password):
    flash('Password incorrect', 'danger')  # Leaks info
```

### Logging Best Practices
```python
import logging

# ✅ GOOD - Log errors without sensitive data
app.logger.error(f'Failed login attempt for username: {username}')

# ❌ BAD - Log sensitive data
app.logger.info(f'User {username} logged in with password {password}')  # NEVER
```

## Security Headers

### Recommended Headers
```python
# In app/__init__.py
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

## Rate Limiting

### Flask-Limiter (Optional)
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to specific routes
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Prevent brute force
def login():
    pass
```

## Security Testing Checklist

### Before Committing Changes

- [ ] All forms include CSRF tokens (`{{ form.hidden_tag() }}`)
- [ ] Protected routes use `@login_required`
- [ ] Admin routes use `@require_role('admin')`
- [ ] File uploads use `secure_filename()`
- [ ] File uploads validate file type
- [ ] Passwords are hashed with bcrypt (via `user.set_password()`)
- [ ] No secrets hardcoded in code
- [ ] SQLAlchemy ORM used (no raw SQL with user input)
- [ ] User input not rendered with `|safe` filter
- [ ] Error messages don't leak sensitive information
- [ ] Access control checks for resource ownership

### Testing Security

```python
# Test authentication required
def test_route_requires_auth(client):
    response = client.get('/admin')
    assert response.status_code == 302  # Redirect to login

# Test authorization required
def test_route_requires_admin(client, regular_user):
    # Login as non-admin
    client.post('/login', data={'username': 'testuser', 'password': 'password123'})
    response = client.get('/admin')
    assert response.status_code == 403  # Forbidden

# Test CSRF protection
def test_csrf_required(csrf_client):
    response = csrf_client.post('/login', data={'username': 'test', 'password': 'test'})
    assert response.status_code == 400  # Bad request (missing CSRF token)

# Test file upload validation
def test_invalid_file_rejected(client, mock_invalid_file):
    response = client.post('/post/new', data={'portrait': mock_invalid_file})
    assert b'Invalid file type' in response.data
```

## Common Vulnerabilities & Prevention

| Vulnerability | Prevention | Status |
|---------------|------------|--------|
| SQL Injection | Use SQLAlchemy ORM, never raw SQL with user input | ✅ Implemented |
| XSS | Jinja2 auto-escaping, avoid `\|safe` on user input | ✅ Implemented |
| CSRF | Flask-WTF CSRF protection, tokens in all forms | ✅ Implemented |
| Weak Passwords | Bcrypt hashing, password complexity requirements | ✅ Implemented |
| Directory Traversal | `secure_filename()` on all uploads | ✅ Implemented |
| Unauthorized Access | `@login_required`, `@require_role()` decorators | ✅ Implemented |
| File Upload Abuse | File type validation, size limits, image verification | ✅ Implemented |
| Session Hijacking | HttpOnly cookies, SameSite, HTTPS in production | ✅ Implemented |
| Information Disclosure | Generic error messages, no secret logging | ✅ Implemented |
| Clickjacking | X-Frame-Options header | ⚠️ Recommended |
| Rate Limiting | Flask-Limiter on auth routes | ⚠️ Optional |

## Security Auditing

### Manual Code Review
Use security-auditor agent before committing:
```
security-auditor, review [feature] for:
- Authentication/authorization
- Input validation
- File upload security
- SQL injection vectors
- XSS risks
```

### Automated Testing
```bash
# Run security-focused tests
pytest tests/ -m security -v

# Check for hardcoded secrets (example using truffleHog)
trufflehog filesystem . --only-verified

# Static analysis (example using bandit)
bandit -r app/
```

## Agent Touchpoints

### security-auditor
- Needs: All security patterns, vulnerability prevention strategies, testing methods
- Common tasks: Reviewing auth flows, validating CSRF protection, checking upload security
- Key files: app/routes/*.py, app/models/*.py, app/templates/*.html

### code-reviewer-pro
- Needs: Security checklist, common pitfalls, best practices
- Common tasks: Pre-commit security review, validating access controls
- Key files: All route and model files

### python-pro
- Needs: Secure coding patterns, bcrypt usage, ORM patterns
- Common tasks: Implementing secure features, optimizing security code
- Key files: app/models/user.py, app/utils/decorators.py

### test-automator
- Needs: Security testing patterns, auth testing, CSRF testing
- Common tasks: Writing security tests, expanding security coverage
- Key files: tests/test_auth_decorators.py, tests/test_routes_*.py

## Related Documentation
- `CLAUDE.md` - Development workflow and agent usage
- `tests/CONTEXT.md` - Security testing patterns
- `app/routes/CONTEXT.md` - Route security requirements
- `app/models/CONTEXT.md` - Model security (password hashing)
