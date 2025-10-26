"""
Tests for admin role CRUD operations (TC-55).

Tests cover:
- POST /admin/roles/create - Create new role via AJAX (JSON)
- POST /admin/update_role - AJAX in-line role update
- POST /admin/roles/<id>/delete - Delete role
- Authentication and authorization requirements
- JSON validation (name, description, badge color)
- Role assignment protection (cannot delete roles assigned to users)
"""

import pytest
import json
from flask import url_for
from app.models import Role, User
from app import db


class TestRoleCreation:
    """Tests for creating roles via AJAX."""

    def test_create_role_requires_authentication(self, client, app):
        """Test unauthenticated access is denied."""
        with app.app_context():
            response = client.post(
                url_for('admin.create_role'),
                json={'name': 'test', 'badge_color': '#000000'},
                content_type='application/json'
            )
            assert response.status_code == 302  # Redirect to login

    def test_create_role_regular_user_denied(self, auth_client, app):
        """Test regular user cannot create roles."""
        with app.app_context():
            response = auth_client.post(
                url_for('admin.create_role'),
                json={'name': 'test', 'badge_color': '#000000'},
                content_type='application/json'
            )
            assert response.status_code == 403  # Forbidden

    def test_create_role_success(self, admin_client, app):
        """Test successfully creating a new role via AJAX."""
        with app.app_context():
            data = {
                'name': 'editor',
                'description': 'Can edit content',
                'badge_color': '#FF5733'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 201
            response_data = response.get_json()
            assert response_data['status'] == 'success'
            assert response_data['role']['name'] == 'editor'
            assert response_data['role']['description'] == 'Can edit content'
            assert response_data['role']['badge_color'] == '#FF5733'

            # Check role was created in database
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
                'badge_color': '#FF5733'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data['status'] == 'error'
            assert 'already exists' in response_data['message']

    def test_create_role_invalid_hex_color(self, admin_client, app):
        """Test creating role with invalid hex color fails."""
        with app.app_context():
            data = {
                'name': 'tester',
                'description': 'Test role',
                'badge_color': 'invalid-color'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data['status'] == 'error'
            assert 'Invalid hex color format' in response_data['message']

    def test_create_role_short_name(self, admin_client, app):
        """Test creating role with name too short fails."""
        with app.app_context():
            data = {
                'name': 'a',  # Too short (min 2)
                'description': 'Test role',
                'badge_color': '#FF5733'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data['status'] == 'error'
            assert 'at least 2 characters' in response_data['message']

    def test_create_role_long_description(self, admin_client, app):
        """Test creating role with description too long fails."""
        with app.app_context():
            data = {
                'name': 'test_role',
                'description': 'x' * 201,  # Too long (max 200)
                'badge_color': '#FF5733'
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data['status'] == 'error'
            assert 'must not exceed 200 characters' in response_data['message']


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
            deleted_role = db.session.get(Role, role_id)
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
            role = db.session.get(Role, admin_role.id)
            assert role is not None

    def test_delete_role_nonexistent(self, admin_client, app):
        """Test deleting non-existent role returns 404."""
        with app.app_context():
            data = {'csrf_token': 'test_token'}
            response = admin_client.post(url_for('admin.delete_role', role_id=9999), data=data)
            assert response.status_code == 404


class TestRoleFormValidation:
    """Tests for role JSON validation."""

    def test_hex_color_validation_3_digit(self, admin_client, app):
        """Test 3-digit hex color is accepted (#RGB)."""
        with app.app_context():
            data = {
                'name': 'rgb_test',
                'description': 'Test 3-digit hex',
                'badge_color': '#F0A'  # Valid 3-digit hex
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 201
            role = Role.query.filter_by(name='rgb_test').first()
            assert role is not None
            assert role.badge_color == '#F0A'

    def test_hex_color_validation_6_digit(self, admin_client, app):
        """Test 6-digit hex color is accepted (#RRGGBB)."""
        with app.app_context():
            data = {
                'name': 'rrggbb_test',
                'description': 'Test 6-digit hex',
                'badge_color': '#FF00AA'  # Valid 6-digit hex
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 201
            role = Role.query.filter_by(name='rrggbb_test').first()
            assert role is not None
            assert role.badge_color == '#FF00AA'

    def test_hex_color_validation_missing_hash(self, admin_client, app):
        """Test hex color without # is rejected."""
        with app.app_context():
            data = {
                'name': 'no_hash_test',
                'description': 'Test missing hash',
                'badge_color': 'FF00AA'  # Missing #
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data['status'] == 'error'
            assert 'Invalid hex color format' in response_data['message']

    def test_hex_color_validation_invalid_chars(self, admin_client, app):
        """Test hex color with invalid characters is rejected."""
        with app.app_context():
            data = {
                'name': 'invalid_chars_test',
                'description': 'Test invalid chars',
                'badge_color': '#GGGGGG'  # Invalid chars (G is not hex)
            }

            response = admin_client.post(
                url_for('admin.create_role'),
                json=data,
                content_type='application/json'
            )

            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data['status'] == 'error'
            assert 'Invalid hex color format' in response_data['message']


class TestInlineRoleUpdate:
    """Tests for AJAX in-line role update endpoint."""

    def test_update_role_requires_authentication(self, client, app):
        """Test unauthenticated access is denied."""
        with app.app_context():
            response = client.post(
                url_for('admin.update_role', role_id=1),
                json={'name': 'test', 'badge_color': '#000000'}
            )
            assert response.status_code == 302  # Redirect to login

    def test_update_role_regular_user_denied(self, auth_client, admin_role, app):
        """Test regular user cannot update roles."""
        with app.app_context():
            response = auth_client.post(
                url_for('admin.update_role', role_id=admin_role.id),
                json={'name': 'test', 'badge_color': '#000000'}
            )
            assert response.status_code == 403  # Forbidden

    def test_update_role_success(self, admin_client, app):
        """Test successfully updating a role via AJAX."""
        with app.app_context():
            # Create a role to update
            role = Role(name='moderator', description='Old description', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            # Update role via AJAX
            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'moderator_updated',
                    'description': 'New description',
                    'badge_color': '#ABCDEF'
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['role']['name'] == 'moderator_updated'
            assert data['role']['description'] == 'New description'
            assert data['role']['badge_color'] == '#ABCDEF'

            # Verify database was updated
            updated_role = db.session.get(Role, role_id)
            assert updated_role.name == 'moderator_updated'
            assert updated_role.description == 'New description'
            assert updated_role.badge_color == '#ABCDEF'

    def test_update_role_empty_description(self, admin_client, app):
        """Test updating role with empty description sets it to None."""
        with app.app_context():
            role = Role(name='test_role', description='Original', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'test_role',
                    'description': '',  # Empty description
                    'badge_color': '#123456'
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            updated_role = db.session.get(Role, role_id)
            assert updated_role.description is None

    def test_update_role_missing_data(self, admin_client, app):
        """Test update fails with missing required fields."""
        with app.app_context():
            # Missing badge_color
            response = admin_client.post(
                url_for('admin.update_role', role_id=1),
                json={'name': 'test'},
                content_type='application/json'
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'Missing required fields' in data['message']

    def test_update_role_no_json_data(self, admin_client, app):
        """Test update fails when empty JSON data provided."""
        with app.app_context():
            # Send properly-formed request with correct header but empty body
            response = admin_client.post(
                url_for('admin.update_role', role_id=1),
                json={},  # Empty JSON object
                content_type='application/json'
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'No data provided' in data['message']

    def test_update_role_nonexistent(self, admin_client, app):
        """Test updating non-existent role returns 404."""
        with app.app_context():
            response = admin_client.post(
                url_for('admin.update_role', role_id=9999),
                json={
                    'name': 'test',
                    'description': 'test',
                    'badge_color': '#000000'
                },
                content_type='application/json'
            )

            assert response.status_code == 404
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'Role not found' in data['message']

    def test_update_role_duplicate_name(self, admin_client, admin_role, app):
        """Test updating role to duplicate name fails."""
        with app.app_context():
            # Create another role
            role = Role(name='editor', description='Editor role', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            # Try to rename to admin role's name
            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': admin_role.name,  # Duplicate name
                    'description': 'Description',
                    'badge_color': '#ABCDEF'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'already exists' in data['message']

    def test_update_role_name_too_short(self, admin_client, app):
        """Test updating role with name too short fails."""
        with app.app_context():
            role = Role(name='test_role', description='Test', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'a',  # Too short (min 2)
                    'description': 'Test',
                    'badge_color': '#123456'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'between 2 and 50 characters' in data['message']

    def test_update_role_name_too_long(self, admin_client, app):
        """Test updating role with name too long fails."""
        with app.app_context():
            role = Role(name='test_role', description='Test', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'x' * 51,  # Too long (max 50)
                    'description': 'Test',
                    'badge_color': '#123456'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'between 2 and 50 characters' in data['message']

    def test_update_role_description_too_long(self, admin_client, app):
        """Test updating role with description too long fails."""
        with app.app_context():
            role = Role(name='test_role', description='Test', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'test_role',
                    'description': 'x' * 201,  # Too long (max 200)
                    'badge_color': '#123456'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'must not exceed 200 characters' in data['message']

    def test_update_role_invalid_hex_color(self, admin_client, app):
        """Test updating role with invalid hex color fails."""
        with app.app_context():
            role = Role(name='test_role', description='Test', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'test_role',
                    'description': 'Test',
                    'badge_color': 'not-a-color'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'Invalid hex color format' in data['message']

    def test_update_role_valid_3_digit_hex(self, admin_client, app):
        """Test updating role with valid 3-digit hex color succeeds."""
        with app.app_context():
            role = Role(name='test_role', description='Test', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'test_role',
                    'description': 'Test',
                    'badge_color': '#F0A'  # Valid 3-digit hex
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['role']['badge_color'] == '#F0A'

    def test_update_role_valid_6_digit_hex(self, admin_client, app):
        """Test updating role with valid 6-digit hex color succeeds."""
        with app.app_context():
            role = Role(name='test_role', description='Test', badge_color='#123456')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

            response = admin_client.post(
                url_for('admin.update_role', role_id=role_id),
                json={
                    'name': 'test_role',
                    'description': 'Test',
                    'badge_color': '#FF00AA'  # Valid 6-digit hex
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['role']['badge_color'] == '#FF00AA'
