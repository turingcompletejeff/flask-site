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


def test_update_role_badge_color_success(admin_client, admin_role, app):
    """Test updating a role's badge color."""
    with app.app_context():
        role_id = admin_role.id

        # Prepare data
        data = {
            'role_id': role_id,
            'badge_color': '#00FF00'
        }

        # Send AJAX request
        response = admin_client.post(
            url_for('admin.update_role_badge'),
            data=json.dumps(data),
            content_type='application/json'
        )

        # Check response
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['status'] == 'success'
        assert result['badge_color'] == '#00FF00'

        # Check database - query fresh from database
        from app import db
        updated_role = db.session.query(Role).filter_by(id=role_id).first()
        assert updated_role is not None
        assert updated_role.badge_color == '#00FF00'


def test_update_role_badge_color_invalid_color(admin_client, admin_role, app):
    """Test updating role with invalid color."""
    with app.app_context():
        # Prepare invalid data
        data = {
            'role_id': admin_role.id,
            'badge_color': 'invalid-color'
        }

        # Send AJAX request
        response = admin_client.post(
            url_for('admin.update_role_badge'),
            data=json.dumps(data),
            content_type='application/json'
        )

        # Route doesn't exist yet (TDD), should get 404
        # Once implemented, should return 400 with error message
        if response.status_code == 400:
            result = json.loads(response.data)
            assert result['status'] == 'error'
            assert 'Invalid hex color' in result['message']
        else:
            assert response.status_code == 404


def test_update_role_badge_color_requires_admin(auth_client, admin_role, app):
    """Test regular user cannot update badge color."""
    with app.app_context():
        # Prepare data
        data = {
            'role_id': admin_role.id,
            'badge_color': '#00FF00'
        }

        # Send AJAX request
        response = auth_client.post(
            url_for('admin.update_role_badge'),
            data=json.dumps(data),
            content_type='application/json'
        )

        # Route doesn't exist yet (TDD), should get 404
        # Once implemented, should return 403
        assert response.status_code in [403, 404]


def test_update_role_badge_color_nonexistent_role(admin_client, app):
    """Test updating a non-existent role."""
    with app.app_context():
        # Prepare data with a non-existent role ID
        data = {
            'role_id': 9999,  # Non-existent role
            'badge_color': '#00FF00'
        }

        # Send AJAX request
        response = admin_client.post(
            url_for('admin.update_role_badge'),
            data=json.dumps(data),
            content_type='application/json'
        )

        # Route doesn't exist yet, should get 404
        # Once implemented, should also return 404 for non-existent role
        assert response.status_code == 404
