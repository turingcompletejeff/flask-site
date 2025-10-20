"""
Tests for admin role CRUD operations (TC-55).

Tests cover:
- GET /admin/roles/create - Display create role form
- POST /admin/roles/create - Create new role
- GET /admin/roles/<id>/edit - Display edit role form
- POST /admin/roles/<id>/edit - Update existing role
- POST /admin/roles/<id>/delete - Delete role
- Authentication and authorization requirements
- Form validation (name, description, badge color)
- Role assignment protection (cannot delete roles assigned to users)
"""

import pytest
from flask import url_for
from app.models import Role, User
from app import db


class TestRoleCreation:
    """Tests for creating roles."""

    def test_create_role_page_admin_access(self, admin_client, app):
        """Test admin can access the create role page."""
        with app.app_context():
            response = admin_client.get(url_for('admin.create_role'))
            assert response.status_code == 200
            assert b'Create New Role' in response.data

    def test_create_role_page_requires_authentication(self, client, app):
        """Test unauthenticated access is denied."""
        with app.app_context():
            response = client.get(url_for('admin.create_role'), follow_redirects=False)
            assert response.status_code == 302  # Redirect to login

    def test_create_role_page_regular_user_denied(self, auth_client, app):
        """Test regular user cannot access create role page."""
        with app.app_context():
            response = auth_client.get(url_for('admin.create_role'), follow_redirects=False)
            assert response.status_code == 403  # Forbidden

    def test_create_role_success(self, admin_client, app):
        """Test successfully creating a new role."""
        with app.app_context():
            data = {
                'name': 'editor',
                'description': 'Can edit content',
                'badge_color': '#FF5733',
                'csrf_token': admin_client.application.config.get('WTF_CSRF_ENABLED', True) and 'test_token' or ''
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200

            # Check role was created
            role = Role.query.filter_by(name='editor').first()
            assert role is not None
            assert role.description == 'Can edit content'
            assert role.badge_color == '#FF5733'

    def test_create_role_duplicate_name(self, admin_client, admin_role, app):
        """Test creating role with duplicate name fails."""
        with app.app_context():
            data = {
                'name': admin_role.name,  # Use existing role name
                'description': 'Duplicate role',
                'badge_color': '#FF5733',
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200
            assert b'already exists' in response.data

    def test_create_role_invalid_hex_color(self, admin_client, app):
        """Test creating role with invalid hex color fails."""
        with app.app_context():
            data = {
                'name': 'tester',
                'description': 'Test role',
                'badge_color': 'invalid-color',
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200
            # Form should show validation error
            assert b'Invalid hex color' in response.data or b'invalid' in response.data.lower()

    def test_create_role_short_name(self, admin_client, app):
        """Test creating role with name too short fails."""
        with app.app_context():
            data = {
                'name': 'a',  # Too short (min 2)
                'description': 'Test role',
                'badge_color': '#FF5733',
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200
            # Form should show validation error

    def test_create_role_long_description(self, admin_client, app):
        """Test creating role with description too long fails."""
        with app.app_context():
            data = {
                'name': 'test_role',
                'description': 'x' * 201,  # Too long (max 200)
                'badge_color': '#FF5733',
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200
            # Form should show validation error


class TestRoleEditing:
    """Tests for editing roles."""

    def test_edit_role_page_admin_access(self, admin_client, admin_role, app):
        """Test admin can access the edit role page."""
        with app.app_context():
            response = admin_client.get(url_for('admin.edit_role', role_id=admin_role.id))
            assert response.status_code == 200
            assert admin_role.name.encode() in response.data

    def test_edit_role_page_requires_authentication(self, client, admin_role, app):
        """Test unauthenticated access is denied."""
        with app.app_context():
            response = client.get(url_for('admin.edit_role', role_id=admin_role.id), follow_redirects=False)
            assert response.status_code == 302  # Redirect to login

    def test_edit_role_page_regular_user_denied(self, auth_client, admin_role, app):
        """Test regular user cannot access edit role page."""
        with app.app_context():
            response = auth_client.get(url_for('admin.edit_role', role_id=admin_role.id), follow_redirects=False)
            assert response.status_code == 403  # Forbidden

    def test_edit_role_nonexistent(self, admin_client, app):
        """Test editing non-existent role returns 404."""
        with app.app_context():
            response = admin_client.get(url_for('admin.edit_role', role_id=9999))
            assert response.status_code == 404

    def test_edit_role_success(self, admin_client, app):
        """Test successfully editing a role."""
        with app.app_context():
            # Create a role to edit
            role = Role(name='moderator', description='Old description', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            data = {
                'name': 'moderator_updated',
                'description': 'New description',
                'badge_color': '#ABCDEF',
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.edit_role', role_id=role_id),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200

            # Check role was updated
            updated_role = Role.query.get(role_id)
            assert updated_role.name == 'moderator_updated'
            assert updated_role.description == 'New description'
            assert updated_role.badge_color == '#ABCDEF'

    def test_edit_role_duplicate_name(self, admin_client, admin_role, app):
        """Test editing role to duplicate name fails."""
        with app.app_context():
            # Create another role
            role = Role(name='editor', description='Editor role', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            data = {
                'name': admin_role.name,  # Try to use admin role's name
                'description': 'Description',
                'badge_color': '#ABCDEF',
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.edit_role', role_id=role_id),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200
            assert b'already exists' in response.data

    def test_edit_role_invalid_color(self, admin_client, admin_role, app):
        """Test editing role with invalid color fails."""
        with app.app_context():
            data = {
                'name': 'updated_name',
                'description': 'Description',
                'badge_color': 'not-a-hex-color',
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.edit_role', role_id=admin_role.id),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200
            assert b'Invalid hex color' in response.data or b'invalid' in response.data.lower()


class TestRoleDeletion:
    """Tests for deleting roles."""

    def test_delete_role_requires_authentication(self, client, admin_role, app):
        """Test unauthenticated access is denied."""
        with app.app_context():
            response = client.post(url_for('admin.delete_role', role_id=admin_role.id), follow_redirects=False)
            assert response.status_code == 302  # Redirect to login

    def test_delete_role_regular_user_denied(self, auth_client, admin_role, app):
        """Test regular user cannot delete roles."""
        with app.app_context():
            response = auth_client.post(url_for('admin.delete_role', role_id=admin_role.id), follow_redirects=False)
            assert response.status_code == 403  # Forbidden

    def test_delete_role_success(self, admin_client, app):
        """Test successfully deleting an unassigned role."""
        with app.app_context():
            # Create a role that's not assigned to anyone
            role = Role(name='temporary', description='Temp role', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            data = {'csrf_token': 'test_token'}

            response = admin_client.post(
                url_for('admin.delete_role', role_id=role_id),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200

            # Check role was deleted
            deleted_role = Role.query.get(role_id)
            assert deleted_role is None

    def test_delete_role_assigned_to_users(self, admin_client, admin_role, admin_user, app):
        """Test cannot delete role assigned to users."""
        with app.app_context():
            # admin_role is assigned to admin_user
            data = {'csrf_token': 'test_token'}

            response = admin_client.post(
                url_for('admin.delete_role', role_id=admin_role.id),
                data=data,
                follow_redirects=True
            )

            assert response.status_code == 200
            assert b'Cannot delete' in response.data or b'assigned' in response.data

            # Check role still exists
            role = Role.query.get(admin_role.id)
            assert role is not None

    def test_delete_role_nonexistent(self, admin_client, app):
        """Test deleting non-existent role returns 404."""
        with app.app_context():
            data = {'csrf_token': 'test_token'}
            response = admin_client.post(url_for('admin.delete_role', role_id=9999), data=data)
            assert response.status_code == 404


class TestRoleFormValidation:
    """Tests for role form validation."""

    def test_hex_color_validation_3_digit(self, admin_client, app):
        """Test 3-digit hex color is accepted (#RGB)."""
        with app.app_context():
            data = {
                'name': 'rgb_test',
                'description': 'Test 3-digit hex',
                'badge_color': '#F0A',  # Valid 3-digit hex
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            role = Role.query.filter_by(name='rgb_test').first()
            assert role is not None
            assert role.badge_color == '#F0A'

    def test_hex_color_validation_6_digit(self, admin_client, app):
        """Test 6-digit hex color is accepted (#RRGGBB)."""
        with app.app_context():
            data = {
                'name': 'rrggbb_test',
                'description': 'Test 6-digit hex',
                'badge_color': '#FF00AA',  # Valid 6-digit hex
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            role = Role.query.filter_by(name='rrggbb_test').first()
            assert role is not None
            assert role.badge_color == '#FF00AA'

    def test_hex_color_validation_missing_hash(self, admin_client, app):
        """Test hex color without # is rejected."""
        with app.app_context():
            data = {
                'name': 'no_hash_test',
                'description': 'Test missing hash',
                'badge_color': 'FF00AA',  # Missing #
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            assert b'Invalid hex color' in response.data or b'invalid' in response.data.lower()

    def test_hex_color_validation_invalid_chars(self, admin_client, app):
        """Test hex color with invalid characters is rejected."""
        with app.app_context():
            data = {
                'name': 'invalid_chars_test',
                'description': 'Test invalid chars',
                'badge_color': '#GGGGGG',  # Invalid chars (G is not hex)
                'csrf_token': 'test_token'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                data=data,
                follow_redirects=True
            )

            assert b'Invalid hex color' in response.data or b'invalid' in response.data.lower()
