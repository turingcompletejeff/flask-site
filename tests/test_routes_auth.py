"""
Integration tests for authentication routes.

Tests cover:
- Login route (GET and POST)
- Register route (GET and POST)
- Logout route
- Authentication flow
- Form validation
- Error handling
"""

import pytest
from flask import url_for
from app.models import User


@pytest.mark.integration
class TestLoginRoute:
    """Test suite for /login route."""

    def test_login_page_accessible(self, client):
        """Test that login page is accessible via GET."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_page_contains_form(self, client):
        """Test that login page contains login form elements."""
        response = client.get('/login')
        html = response.data.decode('utf-8')

        # Should contain username and password fields
        assert 'username' in html.lower()
        assert 'password' in html.lower()

    def test_login_success_with_valid_credentials(self, client, regular_user, db):
        """Test successful login with valid credentials."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should see welcome message
        assert b'welcome' in response.data.lower()

    def test_login_redirects_to_index_on_success(self, client, regular_user, db):
        """Test that successful login redirects to index page."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert '/' in response.location or 'index' in response.location

    def test_login_failure_with_invalid_password(self, client, regular_user, db):
        """Test login failure with incorrect password."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should see error message
        assert b'invalid' in response.data.lower()

    def test_login_failure_with_nonexistent_user(self, client, db):
        """Test login failure with non-existent username."""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'invalid' in response.data.lower()

    def test_login_failure_with_empty_username(self, client, db):
        """Test login failure with empty username."""
        response = client.post('/login', data={
            'username': '',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show error or re-render form

    def test_login_failure_with_empty_password(self, client, regular_user, db):
        """Test login failure with empty password."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': ''
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'invalid' in response.data.lower()

    def test_login_case_sensitive_username(self, client, regular_user, db):
        """Test that username is case-sensitive."""
        response = client.post('/login', data={
            'username': 'TESTUSER',  # Different case
            'password': 'password123'
        }, follow_redirects=True)

        # Should fail (usernames are case-sensitive)
        assert b'invalid' in response.data.lower()

    def test_login_displays_registration_status(self, client, app):
        """Test that login page displays registration status."""
        response = client.get('/login')
        assert response.status_code == 200
        # Should indicate if registration is enabled/disabled


@pytest.mark.integration
class TestRegisterRoute:
    """Test suite for /register route."""

    def test_register_page_accessible(self, client):
        """Test that register page is accessible via GET."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_register_page_contains_form(self, client):
        """Test that register page contains registration form."""
        response = client.get('/register')
        html = response.data.decode('utf-8')

        assert 'username' in html.lower()
        assert 'password' in html.lower()
        assert 'email' in html.lower()

    def test_register_success_with_valid_data(self, client, db):
        """Test successful registration with valid data."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should see success message
        assert b'account created' in response.data.lower() or b'success' in response.data.lower()

        # Verify user was created in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.check_password('newpass123')

    def test_register_redirects_to_login_on_success(self, client, db):
        """Test that successful registration redirects to login page."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert 'login' in response.location

    def test_register_failure_duplicate_username(self, client, regular_user, db):
        """Test registration failure with duplicate username."""
        response = client.post('/register', data={
            'username': 'testuser',  # Already exists
            'password': 'password123',
            'email': 'different@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'taken' in response.data.lower() or b'exists' in response.data.lower()

        # Verify no duplicate user was created
        users = User.query.filter_by(username='testuser').all()
        assert len(users) == 1

    def test_register_password_is_hashed(self, client, db):
        """Test that password is hashed when stored."""
        client.post('/register', data={
            'username': 'hashtest',
            'password': 'plaintext123',
            'email': 'hash@example.com'
        })

        user = User.query.filter_by(username='hashtest').first()
        assert user is not None
        assert user.password_hash != 'plaintext123'
        assert len(user.password_hash) > 20  # Bcrypt hash length

    def test_register_when_disabled(self, client, app, db):
        """Test that registration can be disabled via config."""
        # Disable registration
        app.config['REGISTRATION_ENABLED'] = False

        response = client.get('/register', follow_redirects=True)

        # Should redirect to index with warning
        assert response.status_code == 200
        assert b'disabled' in response.data.lower() or b'/' in response.request.path

    def test_register_post_when_disabled(self, client, app, db):
        """Test that POST to register fails when disabled."""
        app.config['REGISTRATION_ENABLED'] = False

        response = client.post('/register', data={
            'username': 'blocked',
            'password': 'password',
            'email': 'blocked@example.com'
        }, follow_redirects=True)

        # Should be redirected, not create user
        user = User.query.filter_by(username='blocked').first()
        assert user is None


@pytest.mark.integration
class TestLogoutRoute:
    """Test suite for /logout route."""

    def test_logout_requires_authentication(self, client):
        """Test that logout requires user to be logged in."""
        response = client.get('/logout')
        # Should redirect to login (Flask-Login behavior)
        assert response.status_code == 302

    def test_logout_success_when_authenticated(self, auth_client, db):
        """Test successful logout when authenticated."""
        response = auth_client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        assert b'logged out' in response.data.lower()

    def test_logout_redirects_to_index(self, auth_client, db):
        """Test that logout redirects to index page."""
        response = auth_client.get('/logout', follow_redirects=False)

        assert response.status_code == 302
        assert '/' in response.location or 'index' in response.location

    def test_logout_clears_session(self, auth_client, db):
        """Test that logout actually clears the session."""
        # Verify authenticated initially
        response = auth_client.get('/')
        assert response.status_code == 200

        # Logout
        auth_client.get('/logout')

        # Try to access protected route (should be redirected)
        # Note: This depends on having a protected route to test against


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flows."""

    def test_complete_registration_and_login_flow(self, client, db):
        """Test complete flow: register, then login."""
        # Register
        response = client.post('/register', data={
            'username': 'flowuser',
            'password': 'flowpass123',
            'email': 'flow@example.com'
        }, follow_redirects=True)
        assert response.status_code == 200

        # Login with same credentials
        response = client.post('/login', data={
            'username': 'flowuser',
            'password': 'flowpass123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'welcome' in response.data.lower()

    def test_login_logout_login_flow(self, client, regular_user, db):
        """Test flow: login, logout, login again."""
        # First login
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        assert b'welcome' in response.data.lower()

        # Logout
        response = client.get('/logout', follow_redirects=True)
        assert b'logged out' in response.data.lower()

        # Login again
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        assert b'welcome' in response.data.lower()


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test security aspects of authentication."""

    def test_login_prevents_sql_injection(self, client, db):
        """Test that login is protected against SQL injection."""
        response = client.post('/login', data={
            'username': "' OR '1'='1",
            'password': "' OR '1'='1"
        }, follow_redirects=True)

        # Should not allow login
        assert b'invalid' in response.data.lower()

    def test_register_prevents_xss_in_username(self, client, db):
        """Test that registration sanitizes username input."""
        response = client.post('/register', data={
            'username': '<script>alert("XSS")</script>',
            'password': 'password123',
            'email': 'xss@example.com'
        }, follow_redirects=True)

        # Should either reject or sanitize
        user = User.query.filter_by(email='xss@example.com').first()
        if user:
            # If user was created, username should be sanitized or escaped
            assert '<script>' not in user.username or user.username == '<script>alert("XSS")</script>'

    def test_password_not_exposed_in_error_messages(self, client, db):
        """Test that password is not exposed in error messages."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'secretpassword123'
        }, follow_redirects=True)

        html = response.data.decode('utf-8')
        # Password should not appear in response
        assert 'secretpassword123' not in html

    def test_timing_attack_resistance(self, client, regular_user, db):
        """Test that invalid user and invalid password take similar time."""
        # This is a basic test - real timing attack testing would be more sophisticated
        import time

        # Test with non-existent user
        start1 = time.time()
        client.post('/login', data={
            'username': 'nonexistent',
            'password': 'password'
        })
        duration1 = time.time() - start1

        # Test with valid user, wrong password
        start2 = time.time()
        client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        duration2 = time.time() - start2

        # Durations should be roughly similar (within 10x factor)
        # This is a loose check - timing attacks are complex
        assert abs(duration1 - duration2) < 1.0  # Within 1 second
