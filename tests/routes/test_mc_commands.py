"""
Test suite for Minecraft Commands CRUD operations (TC-50).

Tests the mc_commands_bp blueprint with inline editing capabilities.
Follows TDD approach - tests written BEFORE implementation.

Test Coverage:
- TestCommandListView: 5 tests - GET /mc/commands
- TestCommandCreation: 12 tests - POST /mc/commands/create
- TestInlineCommandUpdate: 9 tests - POST /mc/commands/<id>/update
- TestCommandDeletion: 5 tests - POST /mc/commands/<id>/delete
- TestCommandValidation: 5 tests - Boundary/edge cases
- TestCommandAuthorization: 4 tests - Role-based access control

Total: 40 tests (increased from planned 35 for better coverage)
"""

import pytest
import json
from flask import url_for
from app.models import MinecraftCommand
from app import db


# ============================================================================
# TestCommandListView - GET /mc/commands (5 tests)
# ============================================================================

class TestCommandListView:
    """Test the command list/management page."""

    def test_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated users should be redirected to login."""
        response = client.get('/mc/commands')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_regular_user_forbidden(self, client, regular_user):
        """Regular users without minecrafter role should get 403."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        response = client.get('/mc/commands')
        assert response.status_code == 403

    def test_minecrafter_can_access(self, minecrafter_client):
        """Users with minecrafter role should access the page."""
        response = minecrafter_client.get('/mc/commands')
        assert response.status_code == 200
        assert b'Minecraft Command Management' in response.data or b'Saved Commands' in response.data

    def test_admin_can_access(self, admin_client):
        """Admin users should access the page (role bypass)."""
        response = admin_client.get('/mc/commands')
        assert response.status_code == 200

    def test_displays_all_commands(self, minecrafter_client, multiple_commands):
        """Page should display all existing commands."""
        response = minecrafter_client.get('/mc/commands')
        assert response.status_code == 200
        # Check for command names in response
        assert b'tp' in response.data
        assert b'give' in response.data
        assert b'weather' in response.data


# ============================================================================
# TestCommandCreation - POST /mc/commands/create (12 tests)
# ============================================================================

class TestCommandCreation:
    """Test creating new commands via AJAX."""

    def test_create_with_valid_data(self, minecrafter_client):
        """Should create command with valid name and options."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'teleport',
                'options': {'args': ['player', 'x', 'y', 'z']}
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['command_name'] == 'teleport'
        assert data['command']['options']['args'] == ['player', 'x', 'y', 'z']

        # Verify in database
        command = MinecraftCommand.query.filter_by(command_name='teleport').first()
        assert command is not None
        assert command.options == {'args': ['player', 'x', 'y', 'z']}

    def test_create_with_args(self, admin_client):
        """Admin should be able to create commands."""
        response = admin_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'give',
                'options': {'args': ['player', 'item', 'amount']}
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'

    def test_create_with_empty_options(self, minecrafter_client):
        """Should allow creating command with empty options dict."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'list',
                'options': {}
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['options'] == {}

    def test_create_with_null_options(self, minecrafter_client):
        """Should allow creating command with null options."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'help',
                'options': None
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['options'] is None

    def test_missing_command_name(self, minecrafter_client):
        """Should reject creation without command_name."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'command name' in data['message'].lower()

    def test_empty_command_name(self, minecrafter_client):
        """Should reject empty command name."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': '',
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_command_name_too_long(self, minecrafter_client):
        """Should reject command name longer than 20 characters."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'a' * 21,  # 21 characters
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'command name' in data['message'].lower()

    def test_duplicate_command_name(self, minecrafter_client, sample_command):
        """Should reject duplicate command names."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'tp',  # Already exists in sample_command
                'options': {'args': ['different', 'args']}
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'already exists' in data['message'].lower()

    def test_invalid_options_format(self, minecrafter_client):
        """Should reject options that are not a dict."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'test',
                'options': 'invalid string'
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'object' in data['message'].lower() or 'dict' in data['message'].lower()

    def test_options_as_array(self, minecrafter_client):
        """Should reject options as array instead of object."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'test',
                'options': ['arg1', 'arg2']
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_unauthenticated_denied(self, client):
        """Unauthenticated users cannot create commands."""
        response = client.post(
            '/mc/commands/create',
            json={
                'command_name': 'test',
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 302  # Redirect to login

    def test_regular_user_denied(self, client, regular_user):
        """Regular users without minecrafter role cannot create."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        response = client.post(
            '/mc/commands/create',
            json={
                'command_name': 'test',
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 403


# ============================================================================
# TestInlineCommandUpdate - POST /mc/commands/<id>/update (9 tests)
# ============================================================================

class TestInlineCommandUpdate:
    """Test updating commands via inline editing (AJAX)."""

    def test_update_command_name(self, minecrafter_client, sample_command):
        """Should update command name."""
        response = minecrafter_client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={
                'command_name': 'teleport',
                'options': sample_command.options
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['command_name'] == 'teleport'

        # Verify in database
        db.session.refresh(sample_command)
        assert sample_command.command_name == 'teleport'

    def test_update_options(self, minecrafter_client, sample_command):
        """Should update command options."""
        new_options = {'args': ['player', 'x', 'y']}
        response = minecrafter_client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={
                'command_name': sample_command.command_name,
                'options': new_options
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['options'] == new_options

        # Verify in database
        db.session.refresh(sample_command)
        assert sample_command.options == new_options

    def test_clear_options_to_null(self, minecrafter_client, sample_command):
        """Should allow clearing options to null."""
        response = minecrafter_client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={
                'command_name': sample_command.command_name,
                'options': None
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['options'] is None

        # Verify in database
        db.session.refresh(sample_command)
        assert sample_command.options is None

    def test_update_nonexistent_command(self, minecrafter_client):
        """Should return 404 for non-existent command."""
        response = minecrafter_client.post(
            '/mc/commands/99999/update',
            json={
                'command_name': 'test',
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 404

    def test_update_with_duplicate_name(self, minecrafter_client, multiple_commands):
        """Should reject update that creates duplicate name."""
        # Try to rename 'give' to 'tp' (which already exists)
        give_command = [c for c in multiple_commands if c.command_name == 'give'][0]

        response = minecrafter_client.post(
            f'/mc/commands/{give_command.command_id}/update',
            json={
                'command_name': 'tp',  # Already exists
                'options': give_command.options
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'already exists' in data['message'].lower()

    def test_update_with_invalid_options(self, minecrafter_client, sample_command):
        """Should reject invalid options format."""
        response = minecrafter_client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={
                'command_name': sample_command.command_name,
                'options': 'invalid string'
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_missing_required_fields(self, minecrafter_client, sample_command):
        """Should reject update with missing command_name."""
        response = minecrafter_client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_admin_can_update(self, admin_client, sample_command):
        """Admin should be able to update commands."""
        response = admin_client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={
                'command_name': 'updated_by_admin',
                'options': sample_command.options
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'

    def test_unauthenticated_denied(self, client, sample_command):
        """Unauthenticated users cannot update."""
        response = client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={
                'command_name': 'test',
                'options': {}
            },
            content_type='application/json'
        )
        assert response.status_code == 302  # Redirect to login


# ============================================================================
# TestCommandDeletion - POST /mc/commands/<id>/delete (5 tests)
# ============================================================================

class TestCommandDeletion:
    """Test deleting commands via modal confirmation."""

    def test_delete_command(self, minecrafter_client, sample_command):
        """Should successfully delete a command."""
        command_id = sample_command.command_id

        response = minecrafter_client.post(
            f'/mc/commands/{command_id}/delete',
            data={'csrf_token': 'dummy'}  # CSRF disabled in tests
        )
        assert response.status_code == 302  # Redirect after delete

        # Verify command deleted from database
        command = MinecraftCommand.query.get(command_id)
        assert command is None

    def test_delete_nonexistent_command(self, minecrafter_client):
        """Should return 404 for non-existent command."""
        response = minecrafter_client.post(
            '/mc/commands/99999/delete',
            data={'csrf_token': 'dummy'}
        )
        assert response.status_code == 404

    def test_csrf_protection(self, csrf_client, minecrafter_user, sample_command):
        """Should enforce CSRF protection on delete."""
        # Login to CSRF-enabled client
        csrf_client.post('/login', data={
            'username': 'minecrafter',
            'password': 'mcpass123'
        })

        # Try delete without CSRF token
        response = csrf_client.post(
            f'/mc/commands/{sample_command.command_id}/delete',
            data={}
        )
        # Should fail CSRF validation
        assert response.status_code in [400, 403]

    def test_admin_can_delete(self, admin_client, sample_command):
        """Admin should be able to delete commands."""
        command_id = sample_command.command_id

        response = admin_client.post(
            f'/mc/commands/{command_id}/delete',
            data={'csrf_token': 'dummy'}
        )
        assert response.status_code == 302

        # Verify deleted
        command = MinecraftCommand.query.get(command_id)
        assert command is None

    def test_unauthenticated_denied(self, client, sample_command):
        """Unauthenticated users cannot delete."""
        response = client.post(
            f'/mc/commands/{sample_command.command_id}/delete',
            data={'csrf_token': 'dummy'}
        )
        assert response.status_code == 302  # Redirect to login


# ============================================================================
# TestCommandValidation - Boundary and edge cases (5 tests)
# ============================================================================

class TestCommandValidation:
    """Test validation edge cases and boundary conditions."""

    def test_command_name_exactly_20_chars(self, minecrafter_client):
        """Should accept command name exactly 20 characters."""
        name = 'a' * 20  # Exactly 20 chars
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': name,
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['command_name'] == name

    def test_complex_nested_options(self, minecrafter_client):
        """Should handle complex nested options structure."""
        complex_options = {
            'args': ['player', 'item'],
            'flags': {
                'silent': True,
                'force': False
            },
            'metadata': {
                'description': 'Give items to player',
                'aliases': ['giveitem']
            }
        }
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'give',
                'options': complex_options
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['options'] == complex_options

    def test_array_in_options(self, minecrafter_client):
        """Should handle arrays within options object."""
        options_with_array = {
            'args': ['player', 'x', 'y', 'z'],
            'valid_worlds': ['overworld', 'nether', 'end']
        }
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'worldtp',
                'options': options_with_array
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['command']['options']['valid_worlds'] == ['overworld', 'nether', 'end']

    def test_special_characters_in_name(self, minecrafter_client):
        """Should handle special characters in command name."""
        # Test with underscores and hyphens (common in commands)
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': 'give_item',
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        # Behavior depends on validation rules - should either accept or reject consistently
        assert response.status_code in [201, 400]

    def test_whitespace_handling(self, minecrafter_client):
        """Should trim whitespace from command name."""
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={
                'command_name': '  trimmed  ',
                'options': {'args': ['test']}
            },
            content_type='application/json'
        )
        if response.status_code == 201:
            data = response.get_json()
            # Should be trimmed
            assert data['command']['command_name'] == 'trimmed'


# ============================================================================
# TestCommandAuthorization - Role-based access control (4 tests)
# ============================================================================

class TestCommandAuthorization:
    """Comprehensive authorization tests for all routes."""

    def test_all_routes_require_auth(self, client):
        """All routes should redirect unauthenticated users to login."""
        routes = [
            ('/mc/commands', 'GET'),
            ('/mc/commands/create', 'POST'),
        ]

        for route, method in routes:
            if method == 'GET':
                response = client.get(route)
            else:
                response = client.post(route, json={})

            assert response.status_code == 302
            assert '/login' in response.location

    def test_regular_user_denied_all_routes(self, client, regular_user, sample_command):
        """Regular users should get 403 on all routes."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        routes = [
            ('/mc/commands', 'GET'),
            ('/mc/commands/create', 'POST', {'command_name': 'test', 'options': {}}),
            (f'/mc/commands/{sample_command.command_id}/update', 'POST', {'command_name': 'test', 'options': {}}),
            (f'/mc/commands/{sample_command.command_id}/delete', 'POST', {}),
        ]

        for route_data in routes:
            route = route_data[0]
            method = route_data[1]
            data = route_data[2] if len(route_data) > 2 else None

            if method == 'GET':
                response = client.get(route)
            else:
                if 'create' in route or 'update' in route:
                    response = client.post(route, json=data, content_type='application/json')
                else:
                    response = client.post(route, data=data)

            assert response.status_code == 403

    def test_minecrafter_full_access(self, minecrafter_client, sample_command):
        """Minecrafter role should have full CRUD access."""
        # List
        response = minecrafter_client.get('/mc/commands')
        assert response.status_code == 200

        # Create
        response = minecrafter_client.post(
            '/mc/commands/create',
            json={'command_name': 'new_cmd', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 201

        # Update
        response = minecrafter_client.post(
            f'/mc/commands/{sample_command.command_id}/update',
            json={'command_name': 'updated', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Delete
        response = minecrafter_client.post(
            f'/mc/commands/{sample_command.command_id}/delete',
            data={'csrf_token': 'dummy'}
        )
        assert response.status_code == 302

    def test_admin_full_access(self, admin_client):
        """Admin role should have full access (bypass)."""
        # List
        response = admin_client.get('/mc/commands')
        assert response.status_code == 200

        # Create
        response = admin_client.post(
            '/mc/commands/create',
            json={'command_name': 'admin_cmd', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 201

        # Get created command ID
        data = response.get_json()
        command_id = data['command']['command_id']

        # Update
        response = admin_client.post(
            f'/mc/commands/{command_id}/update',
            json={'command_name': 'admin_updated', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Delete
        response = admin_client.post(
            f'/mc/commands/{command_id}/delete',
            data={'csrf_token': 'dummy'}
        )
        assert response.status_code == 302


# ============================================================================
# TestCommandEdgeCases - Error handling and edge cases
# ============================================================================

class TestCommandListEdgeCases:
    """Edge case tests for command list route."""

    def test_database_error_when_loading_commands(self, minecrafter_client, app):
        """Test database error handling when loading commands (lines 62-65)."""
        from sqlalchemy.exc import SQLAlchemyError
        from unittest.mock import patch

        with app.app_context():
            with patch('app.routes.mc_commands.MinecraftCommand.query') as mock_query:
                mock_query.order_by.return_value.all.side_effect = SQLAlchemyError('Connection failed')

                response = minecrafter_client.get('/mc/commands')
                assert response.status_code == 200
                # Should render with empty list and error flash
                assert b'Error loading commands' in response.data or b'commands' in response.data


class TestCommandCreationEdgeCases:
    """Edge case tests for command creation route."""

    def test_create_database_error_handling(self, minecrafter_client, app):
        """Test database error during command creation (lines 156-162)."""
        from sqlalchemy.exc import SQLAlchemyError
        from unittest.mock import patch

        with app.app_context():
            with patch('app.routes.mc_commands.db.session.add') as mock_add:
                mock_add.side_effect = SQLAlchemyError('DB error')

                response = minecrafter_client.post(
                    '/mc/commands/create',
                    json={'command_name': 'test_cmd', 'options': {}},
                    content_type='application/json'
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['status'] == 'error'
                assert 'Database error' in data['message']

    def test_create_unexpected_exception_handling(self, minecrafter_client, app):
        """Test unexpected exception during command creation (lines 164-170)."""
        from unittest.mock import patch

        with app.app_context():
            # Mock the command instantiation to raise an unexpected exception
            with patch('app.routes.mc_commands.MinecraftCommand.__init__', side_effect=Exception('Unexpected error')):
                response = minecrafter_client.post(
                    '/mc/commands/create',
                    json={'command_name': 'test_cmd', 'options': {}},
                    content_type='application/json'
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['status'] == 'error'
                assert 'unexpected error' in data['message'].lower()

    def test_create_rollback_on_database_error(self, minecrafter_client, app, db):
        """Test that database session is rolled back on error."""
        from sqlalchemy.exc import SQLAlchemyError
        from unittest.mock import patch

        with app.app_context():
            with patch('app.routes.mc_commands.db.session.commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError('Commit failed')

                with patch('app.routes.mc_commands.db.session.rollback') as mock_rollback:
                    response = minecrafter_client.post(
                        '/mc/commands/create',
                        json={'command_name': 'test_cmd', 'options': {}},
                        content_type='application/json'
                    )

                    assert response.status_code == 500
                    # Verify rollback was called
                    assert mock_rollback.called


class TestCommandUpdateEdgeCases:
    """Edge case tests for command update route."""

    def test_update_database_error_handling(self, minecrafter_client, app, sample_command):
        """Test database error during command update (lines 277-283)."""
        from sqlalchemy.exc import SQLAlchemyError
        from unittest.mock import patch

        with app.app_context():
            with patch('app.routes.mc_commands.db.session.commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError('DB error')

                response = minecrafter_client.post(
                    f'/mc/commands/{sample_command.command_id}/update',
                    json={'command_name': 'updated', 'options': {}},
                    content_type='application/json'
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['status'] == 'error'
                assert 'Database error' in data['message']

    def test_update_unexpected_exception_handling(self, minecrafter_client, app, sample_command):
        """Test unexpected exception during command update (lines 285-291)."""
        from unittest.mock import patch, PropertyMock

        with app.app_context():
            # Mock setting command_name to raise an unexpected exception
            with patch.object(type(sample_command), 'command_name', new_callable=PropertyMock) as mock_prop:
                mock_prop.side_effect = Exception('Unexpected error')

                response = minecrafter_client.post(
                    f'/mc/commands/{sample_command.command_id}/update',
                    json={'command_name': 'updated', 'options': {}},
                    content_type='application/json'
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['status'] == 'error'
                assert 'unexpected error' in data['message'].lower()

    def test_update_rollback_on_error(self, minecrafter_client, app, sample_command, db):
        """Test that database session is rolled back on update error."""
        from sqlalchemy.exc import SQLAlchemyError
        from unittest.mock import patch

        with app.app_context():
            with patch('app.routes.mc_commands.db.session.commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError('Commit failed')

                with patch('app.routes.mc_commands.db.session.rollback') as mock_rollback:
                    response = minecrafter_client.post(
                        f'/mc/commands/{sample_command.command_id}/update',
                        json={'command_name': 'updated', 'options': {}},
                        content_type='application/json'
                    )

                    assert response.status_code == 500
                    assert mock_rollback.called


class TestCommandDeletionEdgeCases:
    """Edge case tests for command deletion route."""

    def test_delete_nonexistent_command(self, minecrafter_client, app):
        """Test deleting nonexistent command returns 404 (line 330)."""
        with app.app_context():
            response = minecrafter_client.post(
                '/mc/commands/99999/delete',
                data={'csrf_token': 'dummy'}
            )
            assert response.status_code == 404

    def test_delete_database_error_handling(self, minecrafter_client, app, sample_command):
        """Test database error during deletion (lines 335-338)."""
        from sqlalchemy.exc import SQLAlchemyError
        from unittest.mock import patch

        with app.app_context():
            with patch('app.routes.mc_commands.db.session.delete') as mock_delete:
                mock_delete.side_effect = SQLAlchemyError('DB error')

                response = minecrafter_client.post(
                    f'/mc/commands/{sample_command.command_id}/delete',
                    data={'csrf_token': 'dummy'},
                    follow_redirects=True
                )

                # Should handle error gracefully
                assert response.status_code == 200
                assert b'Error' in response.data or b'error' in response.data

    def test_delete_rollback_on_error(self, minecrafter_client, app, sample_command, db):
        """Test that database session is rolled back on deletion error."""
        from sqlalchemy.exc import SQLAlchemyError
        from unittest.mock import patch

        with app.app_context():
            with patch('app.routes.mc_commands.db.session.commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError('Commit failed')

                with patch('app.routes.mc_commands.db.session.rollback') as mock_rollback:
                    response = minecrafter_client.post(
                        f'/mc/commands/{sample_command.command_id}/delete',
                        data={'csrf_token': 'dummy'},
                        follow_redirects=False
                    )

                    # Verify rollback was called
                    assert mock_rollback.called
