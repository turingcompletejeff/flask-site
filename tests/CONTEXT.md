# Testing Standards & Guide

## Overview
Comprehensive testing framework using pytest for unit, integration, and end-to-end tests. Uses SQLite in-memory database for fast, isolated test execution.

## Test Organization

### Test Files Structure
```
tests/
├── conftest.py              # Fixtures and test configuration
├── test_models.py           # Database model unit tests
├── test_routes_*.py         # Route integration tests
├── test_auth_decorators.py  # Authentication/authorization tests
└── test_*.py                # Additional test modules
```

### File Naming Convention
- `test_*.py` - All test files must start with `test_`
- `test_models.py` - Model unit tests
- `test_routes_<blueprint>.py` - Route tests per blueprint (e.g., `test_routes_admin.py`)
- `test_<feature>.py` - Feature-specific tests (e.g., `test_role_validation.py`)

### Test Class Organization
```python
@pytest.mark.unit
class TestUser:
    """Test suite for User model."""

    def test_user_creation(self, db):
        """Test basic user creation."""
        # Test implementation

    def test_password_hashing(self, db):
        """Test password hashing."""
        # Test implementation
```

**Naming Patterns:**
- Classes: `TestModelName` or `TestFeatureName`
- Methods: `test_<what_is_being_tested>` (descriptive, snake_case)
- Always include docstrings explaining what is tested

## Pytest Markers

### Available Markers
```python
@pytest.mark.unit         # Unit tests (models, utilities)
@pytest.mark.integration  # Integration tests (routes, blueprints)
@pytest.mark.slow         # Slow-running tests
@pytest.mark.security     # Security-focused tests
```

### Running Tests by Marker
```bash
# Activate venv first
source venv/bin/activate

# Run only unit tests
pytest tests/ -m unit -v

# Run only integration tests
pytest tests/ -m integration -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

## Fixtures Reference

### Application Fixtures

#### `app` (function scope)
Test Flask application with CSRF disabled for easier testing.
```python
def test_something(app):
    assert app.config['TESTING'] is True
```

#### `csrf_app` (function scope)
Test Flask application with CSRF **enabled** for testing CSRF protection.
```python
def test_csrf_protection(csrf_app):
    # Test CSRF token handling
```

#### `db` (function scope)
Fresh database instance for each test. Creates all tables before test, drops after.
```python
def test_database_operation(db):
    user = User(username='test')
    db.session.add(user)
    db.session.commit()
```

### Client Fixtures

#### `client` (function scope)
Unauthenticated test client for public route testing.
```python
def test_public_route(client):
    response = client.get('/')
    assert response.status_code == 200
```

#### `auth_client` (function scope)
Authenticated as regular user (username: `testuser`, password: `password123`).
```python
def test_authenticated_route(auth_client):
    response = auth_client.get('/profile')
    assert response.status_code == 200
```

#### `blogger_client` (function scope)
Authenticated as blogger (username: `blogger`, password: `blogpass123`).
```python
def test_blogger_route(blogger_client):
    response = blogger_client.get('/post/new')
    assert response.status_code == 200
```

#### `admin_client` (function scope)
Authenticated as admin (username: `admin`, password: `adminpass123`).
```python
def test_admin_route(admin_client):
    response = admin_client.get('/admin')
    assert response.status_code == 200
```

#### `csrf_client` (function scope)
Test client with CSRF protection enabled.
```python
def test_csrf_token(csrf_client):
    response = csrf_client.get('/login')
    token = extract_csrf_token(response)
    assert token is not None
```

### User Fixtures

#### `regular_user`
User without special roles.
- Username: `testuser`
- Password: `password123`
- Email: `test@example.com`

#### `blogger_user`
User with blogger role.
- Username: `blogger`
- Password: `blogpass123`
- Email: `blogger@example.com`

#### `admin_user`
User with admin role.
- Username: `admin`
- Password: `adminpass123`
- Email: `admin@example.com`

### Role Fixtures

#### `admin_role`
Admin role with full access.

#### `blogger_role`
Blogger role for creating/managing blog posts.

### BlogPost Fixtures

#### `published_post`
Published blog post (is_draft=False).
- Title: "Test Published Post"
- Content: "This is a published post."

#### `draft_post`
Draft blog post (is_draft=True).
- Title: "Test Draft Post"
- Content: "This is a draft post."

#### `post_with_images`
Blog post with portrait and thumbnail images.
- Title: "Post with Images"
- Portrait: "test_portrait.jpg"
- Thumbnail: "test_thumb.jpg"

### File Upload Fixtures

#### `mock_image_file`
Mock JPEG image file for testing file uploads.
```python
def test_image_upload(client, mock_image_file):
    response = client.post('/post/new', data={
        'portrait': mock_image_file,
        'title': 'Test',
        'content': 'Content'
    })
```

#### `mock_invalid_file`
Mock invalid file (text file) for testing upload validation.
```python
def test_invalid_file_rejection(client, mock_invalid_file):
    response = client.post('/post/new', data={
        'portrait': mock_invalid_file
    })
    assert b'Invalid file type' in response.data
```

### Context Fixtures

#### `app_context`
Provides application context for tests that need it.
```python
def test_with_app_context(app_context):
    # Code runs inside app context
    from flask import current_app
    assert current_app.config['TESTING'] is True
```

#### `request_context`
Provides request context for tests that need it.
```python
def test_with_request_context(request_context):
    from flask import request
    # Test request-dependent code
```

### Mock Fixtures

#### `mock_rcon`
Mock RCON connection for Minecraft integration tests.
```python
from unittest.mock import patch

def test_minecraft_command(client, mock_rcon):
    with patch('app.routes.mc.rcon', mock_rcon):
        response = client.post('/mc/command', data={'cmd': 'list'})
        assert response.status_code == 200
```

## Testing Patterns

### 1. Model Unit Tests

```python
@pytest.mark.unit
class TestUser:
    """Test suite for User model."""

    def test_user_creation(self, db):
        """Test basic user creation."""
        user = User(username='newuser', email='new@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'newuser'
        assert user.password_hash != 'testpass'  # Should be hashed

    def test_password_hashing(self, regular_user):
        """Test password verification."""
        assert regular_user.check_password('password123') is True
        assert regular_user.check_password('wrongpass') is False
```

### 2. Route Integration Tests

```python
@pytest.mark.integration
class TestAuthRoutes:
    """Test suite for authentication routes."""

    def test_login_success(self, client, regular_user):
        """Test successful login."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Welcome' in response.data

    def test_login_invalid_credentials(self, client, regular_user):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        assert response.status_code == 200
        assert b'Invalid' in response.data
```

### 3. Authorization Tests

```python
@pytest.mark.security
def test_admin_route_requires_admin(self, client, blogger_user):
    """Test that admin routes require admin role."""
    # Login as blogger (not admin)
    client.post('/login', data={
        'username': 'blogger',
        'password': 'blogpass123'
    })

    # Try to access admin route
    response = client.get('/admin')
    assert response.status_code == 403  # Forbidden
```

### 4. CSRF Protection Tests

```python
def test_csrf_token_required(self, csrf_client):
    """Test that CSRF token is required for POST requests."""
    response = csrf_client.post('/login', data={
        'username': 'test',
        'password': 'test'
    })
    # Should fail without CSRF token
    assert response.status_code == 400

def test_csrf_token_valid(self, csrf_client):
    """Test successful POST with valid CSRF token."""
    response = csrf_client.get('/login')
    token = extract_csrf_token(response)

    response = csrf_client.post('/login', data={
        'csrf_token': token,
        'username': 'test',
        'password': 'test'
    })
    # Should succeed with valid token
```

### 5. File Upload Tests

```python
def test_image_upload(self, admin_client, mock_image_file):
    """Test valid image upload."""
    response = admin_client.post('/post/new', data={
        'title': 'Test Post',
        'content': 'Test content',
        'portrait': mock_image_file
    }, content_type='multipart/form-data')

    assert response.status_code == 302  # Redirect on success

def test_invalid_file_rejected(self, admin_client, mock_invalid_file):
    """Test that non-image files are rejected."""
    response = admin_client.post('/post/new', data={
        'portrait': mock_invalid_file
    }, content_type='multipart/form-data')

    assert b'Invalid file type' in response.data
```

### 6. Database Relationship Tests

```python
def test_user_role_relationship(self, db, admin_role):
    """Test many-to-many relationship between users and roles."""
    user = User(username='roletest', email='roletest@example.com')
    user.set_password('password')
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()

    # Test bidirectional relationship
    assert user in admin_role.assigned_users
    assert admin_role in user.roles
```

### 7. Draft Post Access Tests

```python
def test_draft_visible_to_authenticated(self, auth_client, draft_post):
    """Test that authenticated users can see drafts in listing."""
    response = auth_client.get('/')
    assert b'DRAFT' in response.data

def test_draft_hidden_from_public(self, client, draft_post):
    """Test that public users cannot see drafts."""
    response = client.get('/')
    assert b'DRAFT' not in response.data
```

## Running Tests

### Basic Commands

```bash
# ALWAYS activate virtual environment first
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run specific test class
pytest tests/test_models.py::TestUser -v

# Run specific test method
pytest tests/test_models.py::TestUser::test_user_creation -v

# Run with markers
pytest tests/ -m unit -v
pytest tests/ -m integration -v
```

### Coverage Reports

```bash
# Run with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser

# Coverage in terminal
pytest tests/ --cov=app --cov-report=term-missing
```

### Useful Options

```bash
# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l

# Run last failed tests
pytest tests/ --lf

# Run failed tests first, then others
pytest tests/ --ff

# Verbose output with print statements
pytest tests/ -v -s

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto
```

## Writing New Tests

### Step-by-Step Guide

1. **Determine test type:**
   - Model logic → `test_models.py` or new file
   - Route behavior → `test_routes_<blueprint>.py`
   - Auth/security → `test_auth_decorators.py` or `test_routes_*.py`

2. **Create test class:**
```python
@pytest.mark.unit  # or @pytest.mark.integration
class TestNewFeature:
    """Test suite for new feature."""
```

3. **Write test method:**
```python
def test_feature_behavior(self, fixture1, fixture2):
    """Test specific behavior of feature."""
    # Arrange
    user = User(username='test')

    # Act
    result = user.some_method()

    # Assert
    assert result == expected_value
```

4. **Use appropriate fixtures:**
   - Need database? Use `db`
   - Need authenticated user? Use `auth_client`, `blogger_client`, or `admin_client`
   - Need models? Use `regular_user`, `admin_user`, `published_post`, etc.

5. **Add markers:**
```python
@pytest.mark.unit
@pytest.mark.security  # Multiple markers allowed
def test_something(self):
    pass
```

6. **Run your new tests:**
```bash
pytest tests/test_new_file.py -v
```

## Test Coverage Standards

### Minimum Coverage Requirements
- **Models:** 90%+ coverage
- **Routes:** 80%+ coverage
- **Utilities:** 85%+ coverage
- **Overall:** 80%+ coverage

### What to Test

#### Models
- [ ] Object creation and defaults
- [ ] Field validation and constraints
- [ ] Methods and computed properties
- [ ] Relationships (one-to-many, many-to-many)
- [ ] Unique constraints
- [ ] Password hashing (for User model)

#### Routes
- [ ] Successful requests (200, 302)
- [ ] Authentication required (401 redirect)
- [ ] Authorization required (403 forbidden)
- [ ] Invalid input handling (400)
- [ ] CSRF protection on POST routes
- [ ] File upload validation
- [ ] Draft post access controls

#### Forms
- [ ] Valid data acceptance
- [ ] Invalid data rejection
- [ ] Required field validation
- [ ] Custom validators

#### Security
- [ ] Password hashing
- [ ] CSRF tokens on forms
- [ ] Role-based access control
- [ ] SQL injection prevention (use ORM)
- [ ] XSS prevention (test escaping)
- [ ] File upload restrictions

## Common Testing Pitfalls

### ❌ Don't Do This

```python
# Don't hardcode IDs
def test_get_user(client):
    response = client.get('/admin/users/1/edit')  # ID might not exist

# Don't use production database
def test_create_user():
    # Uses actual DATABASE_URL - WRONG!

# Don't forget to commit
def test_user_creation(db):
    user = User(username='test')
    db.session.add(user)
    # Missing db.session.commit()
    assert User.query.count() == 1  # FAILS

# Don't test implementation details
def test_password_hash_format(regular_user):
    assert regular_user.password_hash.startswith('$2b$')  # Too specific
```

### ✅ Do This Instead

```python
# Use fixtures that return objects with IDs
def test_get_user(admin_client, regular_user):
    response = admin_client.get(f'/admin/users/{regular_user.id}/edit')

# Always use test database (handled by conftest.py)
def test_create_user(db):
    # Uses SQLite in-memory via fixture

# Always commit when testing database state
def test_user_creation(db):
    user = User(username='test')
    db.session.add(user)
    db.session.commit()  # ✓
    assert User.query.count() == 1

# Test behavior, not implementation
def test_password_verification(regular_user):
    assert regular_user.check_password('password123') is True
```

## Debugging Failed Tests

### View Detailed Output
```bash
# Show print statements and detailed errors
pytest tests/test_file.py -v -s

# Show local variables on failure
pytest tests/test_file.py -l

# Drop into debugger on failure
pytest tests/test_file.py --pdb
```

### Common Failure Causes

1. **IntegrityError: UNIQUE constraint failed**
   - Cause: Duplicate data in database
   - Solution: Use function-scoped fixtures, check for existing data

2. **AssertionError: assert 302 == 200**
   - Cause: Unexpected redirect (often auth required)
   - Solution: Use authenticated client or check `follow_redirects=True`

3. **KeyError or AttributeError**
   - Cause: Missing data in response or object
   - Solution: Check that fixtures properly set up data

4. **CSRF validation failed**
   - Cause: Testing with CSRF enabled without token
   - Solution: Use `csrf_app` and `extract_csrf_token()` helper

## Agent Touchpoints

### test-automator
- Needs: Fixture patterns, testing standards, coverage requirements
- Common tasks: Writing new test suites, expanding coverage, setting up CI/CD testing
- Key files: conftest.py (fixtures), test_*.py (test implementations)

### qa-expert
- Needs: Test organization, coverage reports, testing strategies
- Common tasks: Designing test plans, identifying edge cases, validating coverage
- Key files: All test files, coverage reports

### security-auditor
- Needs: Security test patterns, auth/CSRF testing, file upload validation
- Common tasks: Writing security tests, validating auth flows, testing access controls
- Key files: test_auth_decorators.py, test_routes_*.py (security-focused tests)

### python-pro
- Needs: Pytest patterns, fixture usage, mocking strategies
- Common tasks: Optimizing test performance, refactoring fixtures, adding complex tests
- Key files: conftest.py, test implementation files

### debugger
- Needs: Test structure, fixture dependencies, common failure patterns
- Common tasks: Diagnosing test failures, fixing flaky tests, debugging database issues
- Key files: All test files, conftest.py

## Best Practices

### Arrange-Act-Assert Pattern
```python
def test_user_login(client, regular_user):
    # Arrange
    login_data = {
        'username': 'testuser',
        'password': 'password123'
    }

    # Act
    response = client.post('/login', data=login_data)

    # Assert
    assert response.status_code == 302
    assert response.location == '/'
```

### Use Descriptive Test Names
```python
# ✅ Good
def test_admin_route_returns_403_for_regular_user(self):

# ❌ Bad
def test_admin(self):
```

### One Assert Per Concept
```python
# ✅ Good - Tests one concept
def test_user_has_admin_role(admin_user):
    assert admin_user.has_role('admin') is True

# ❌ Bad - Tests multiple unrelated things
def test_user(admin_user):
    assert admin_user.username == 'admin'
    assert admin_user.check_password('adminpass123')
    assert admin_user.has_role('admin')
    assert len(admin_user.roles) > 0
```

### Use Fixtures Over Setup/Teardown
```python
# ✅ Good - Use fixtures
def test_with_user(regular_user):
    assert regular_user.username == 'testuser'

# ❌ Avoid - Setup/teardown is less Pythonic
class TestUser:
    def setup_method(self):
        self.user = User(username='test')
```

### Test Edge Cases
```python
def test_password_check_with_empty_string(regular_user):
    """Test password verification with empty password."""
    assert regular_user.check_password('') is False

def test_has_role_with_nonexistent_role(regular_user):
    """Test has_role returns False for non-existent role."""
    assert regular_user.has_role('nonexistent_role') is False
```

## CI/CD Integration

### GitHub Actions Example
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v2
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
source venv/bin/activate
pytest tests/ --cov=app --cov-fail-under=80
```

## Related Documentation
- `conftest.py` - All fixture definitions
- `CLAUDE.md` - Agent workflow and development patterns
- `docs/SECURITY.md` - Security testing patterns
- `app/routes/CONTEXT.md` - Route naming standards for route tests
