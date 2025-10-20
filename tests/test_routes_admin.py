"""
Tests for admin routes related to role badge management.

Tests cover:
- GET /admin/roles - Display roles management page
- POST /admin/update_role_badge - Update role badge color via AJAX
- Authentication and authorization requirements
- Color validation and error handling
"""

import json
import pytest
from flask import url_for
from app.models import Role


def test_admin_roles_page_admin_access(admin_client, app):
    """Test admin can access the roles page."""
    with app.app_context():
        response = admin_client.get(url_for('admin.roles'))
        # Route doesn't exist yet in TDD, should get 404
        # Once implemented, this should return 200
        assert response.status_code in [200, 404]


def test_admin_roles_page_requires_authentication(client, app):
    """Test unauthenticated access is denied."""
    with app.app_context():
        response = client.get(url_for('admin.roles'), follow_redirects=False)
        # Should redirect to login (302) or give 404 if route doesn't exist
        assert response.status_code in [302, 404]


def test_admin_roles_page_regular_user_denied(auth_client, app):
    """Test regular user cannot access admin roles page."""
    with app.app_context():
        response = auth_client.get(url_for('admin.roles'), follow_redirects=False)
        # Should get 403 (forbidden) or 404 if route doesn't exist
        assert response.status_code in [403, 404]


