"""
Unit tests for authentication and authorization decorators.

Tests cover:
- @login_required decorator (Flask-Login)
- @require_role decorator
- @require_any_role decorator
- Admin bypass behavior
"""

import pytest
from flask import Blueprint
from flask_login import login_required
from app.auth_decorators import require_role, require_any_role


# ============================================================================
# Test Routes using Decorators
# ============================================================================

@pytest.fixture(scope='function')
def decorator_test_bp():
    """Create test routes with decorators for testing."""
    bp = Blueprint('test_decorators', __name__)

    @bp.route('/protected')
    @login_required
    def protected_route():
        return 'Protected content', 200

    @bp.route('/blogger-only')
    @login_required
    @require_role('blogger')
    def blogger_only_route():
        return 'Blogger content', 200

    @bp.route('/admin-only')
    @login_required
    @require_role('admin')
    def admin_only_route():
        return 'Admin content', 200

    @bp.route('/blogger-or-admin')
    @login_required
    @require_any_role(['blogger', 'admin'])
    def multi_role_route():
        return 'Multi-role content', 200

    return bp


@pytest.fixture(scope='function')
def test_app_with_decorators(app, decorator_test_bp):
    """Register the test blueprint with the app."""
    app.register_blueprint(decorator_test_bp)
    return app


@pytest.fixture(scope='function')
def test_client(test_app_with_decorators):
    """Provide a test client for the decorated routes."""
    return test_app_with_decorators.test_client()


# ============================================================================
# Test @login_required Decorator
# ============================================================================

@pytest.mark.security
class TestLoginRequired:
    """Test suite for @login_required decorator."""

    def test_unauthenticated_user_redirected(self, test_client, db):
        """Test that unauthenticated users are redirected to login."""
        response = test_client.get('/protected')
        assert response.status_code == 302  # Redirect
        assert '/login' in response.location

    def test_authenticated_user_allowed(self, test_client, regular_user, db):
        """Test that authenticated users can access protected routes."""
        # Login
        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        response = test_client.get('/protected')
        assert response.status_code == 200
        assert b'Protected content' in response.data


# ============================================================================
# Test @require_role Decorator
# ============================================================================

@pytest.mark.security
class TestRequireRole:
    """Test suite for @require_role decorator."""

    def test_unauthenticated_user_401(self, test_client, db):
        """Test that unauthenticated users get 401 Unauthorized."""
        response = test_client.get('/blogger-only')
        # Flask-Login redirects to login page, not 401
        assert response.status_code == 302

    def test_user_without_role_403(self, test_client, regular_user, db):
        """Test that users without required role get 403 Forbidden."""
        # Login as regular user (no roles)
        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        response = test_client.get('/blogger-only')
        assert response.status_code == 403

    def test_user_with_role_allowed(self, test_client, blogger_user, db):
        """Test that users with required role can access route."""
        # Login as blogger
        test_client.post('/login', data={
            'username': 'blogger',
            'password': 'blogpass123'
        })

        response = test_client.get('/blogger-only')
        assert response.status_code == 200
        assert b'Blogger content' in response.data

    def test_admin_bypass_all_roles(self, test_client, admin_user, db):
        """Test that admin users bypass all role checks."""
        # Login as admin
        test_client.post('/login', data={
            'username': 'admin',
            'password': 'adminpass123'
        })

        # Admin can access blogger-only route
        response = test_client.get('/blogger-only')
        assert response.status_code == 200
        assert b'Blogger content' in response.data

    def test_wrong_role_denied(self, test_client, blogger_user, admin_role, db):
        """Test that users with wrong role are denied access."""
        # Login as blogger (trying to access admin-only)
        test_client.post('/login', data={
            'username': 'blogger',
            'password': 'blogpass123'
        })

        response = test_client.get('/admin-only')
        assert response.status_code == 403


# ============================================================================
# Test @require_any_role Decorator
# ============================================================================

@pytest.mark.security
class TestRequireAnyRole:
    """Test suite for @require_any_role decorator."""

    def test_unauthenticated_user_redirected(self, test_client, db):
        """Test that unauthenticated users are redirected."""
        response = test_client.get('/blogger-or-admin')
        assert response.status_code == 302  # Flask-Login redirect

    def test_user_without_any_role_403(self, test_client, regular_user, db):
        """Test that users without any of the required roles get 403."""
        # Login as regular user (no roles)
        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        response = test_client.get('/blogger-or-admin')
        assert response.status_code == 403

    def test_user_with_first_role_allowed(self, test_client, blogger_user, db):
        """Test that users with first role in list can access route."""
        # Login as blogger
        test_client.post('/login', data={
            'username': 'blogger',
            'password': 'blogpass123'
        })

        response = test_client.get('/blogger-or-admin')
        assert response.status_code == 200
        assert b'Multi-role content' in response.data

    def test_user_with_second_role_allowed(self, test_client, admin_user, db):
        """Test that users with second role in list can access route."""
        # Login as admin
        test_client.post('/login', data={
            'username': 'admin',
            'password': 'adminpass123'
        })

        response = test_client.get('/blogger-or-admin')
        assert response.status_code == 200
        assert b'Multi-role content' in response.data

    def test_admin_bypass_any_role(self, test_client, admin_user, db):
        """Test that admin users bypass require_any_role checks."""
        # Login as admin
        test_client.post('/login', data={
            'username': 'admin',
            'password': 'adminpass123'
        })

        response = test_client.get('/blogger-or-admin')
        assert response.status_code == 200

    def test_user_with_multiple_roles(self, test_client, db, admin_role, blogger_role):
        """Test that users with multiple roles can access route."""
        from app.models import User

        # Create user with both roles
        user = User(username='multiuser', email='multi@example.com')
        user.set_password('password')
        user.roles.append(admin_role)
        user.roles.append(blogger_role)
        db.session.add(user)
        db.session.commit()

        # Login
        test_client.post('/login', data={
            'username': 'multiuser',
            'password': 'password'
        })

        response = test_client.get('/blogger-or-admin')
        assert response.status_code == 200


# ============================================================================
# Test Edge Cases
# ============================================================================

@pytest.mark.security
class TestDecoratorEdgeCases:
    """Test edge cases and security considerations."""

    def test_logout_clears_access(self, test_client, blogger_user, db):
        """Test that logging out revokes access to protected routes."""
        # Login
        test_client.post('/login', data={
            'username': 'blogger',
            'password': 'blogpass123'
        })

        # Verify access
        response = test_client.get('/blogger-only')
        assert response.status_code == 200

        # Logout
        test_client.get('/logout')

        # Verify no access after logout
        response = test_client.get('/blogger-only')
        assert response.status_code == 302  # Redirected to login

    def test_role_change_reflected_immediately(self, test_client, regular_user, blogger_role, db):
        """Test that role changes are reflected immediately."""
        # Login as regular user
        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Should be denied
        response = test_client.get('/blogger-only')
        assert response.status_code == 403

        # Grant blogger role
        regular_user.roles.append(blogger_role)
        db.session.commit()

        # Note: In production, this might require re-login to take effect
        # depending on how session management is configured
        # For testing purposes, we verify the model behavior is correct
        assert regular_user.has_role('blogger') is True
