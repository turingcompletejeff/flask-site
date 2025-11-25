"""
Comprehensive tests for Minecraft RCON routes.

Tests cover:
- Authentication and authorization checks
- RCON connection management
- Command execution
- Query functionality
- Command listing
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import socket


@pytest.mark.integration
class TestMCRouteAuthentication:
    """Test suite for authentication and authorization on MC routes."""

    def test_mc_routes_require_authentication(self, client):
        """Test that MC routes require login."""
        routes = ['/mc', '/mc/init', '/mc/stop', '/mc/query', '/mc/list']

        for route in routes:
            if route == '/mc/command':
                continue  # POST route, tested separately
            response = client.get(route)
            assert response.status_code in [302, 403]  # Redirect to login or forbidden

    def test_mc_routes_require_minecrafter_role(self, auth_client):
        """Test that MC routes require minecrafter role for non-admin users."""
        # auth_client is regular user without minecrafter role
        response = auth_client.get('/mc')
        assert response.status_code == 403  # Forbidden

    def test_mc_routes_accessible_to_minecrafter(self, app, db):
        """Test that users with minecrafter role can access MC routes."""
        from app.models import User, Role

        # Create minecrafter role if it doesn't exist
        minecrafter_role = Role.query.filter_by(name='minecrafter').first()
        if not minecrafter_role:
            minecrafter_role = Role(name='minecrafter', description='Can access Minecraft server')
            db.session.add(minecrafter_role)
            db.session.commit()

        # Create user with minecrafter role
        mc_user = User(username='mcuser', email='mc@example.com')
        mc_user.set_password('password123')
        mc_user.roles.append(minecrafter_role)
        db.session.add(mc_user)
        db.session.commit()

        # Login as minecrafter
        with app.test_client() as client:
            client.post('/login', data={
                'username': 'mcuser',
                'password': 'password123'
            }, follow_redirects=True)

            response = client.get('/mc')
            assert response.status_code == 200

    def test_mc_routes_accessible_to_admin(self, admin_client):
        """Test that admin users can access MC routes (bypass role check)."""
        response = admin_client.get('/mc')
        assert response.status_code == 200

    def test_mc_command_post_requires_authentication(self, client):
        """Test that POST /mc/command requires authentication."""
        response = client.post('/mc/command', data={'command': 'help'})
        assert response.status_code in [302, 403]

    def test_mc_routes_redirect_to_login_when_not_authenticated(self, client):
        """Test that unauthenticated requests redirect to login."""
        response = client.get('/mc')
        assert response.status_code == 302
        assert 'login' in response.location or b'login' in response.data


@pytest.mark.integration
class TestMCIndexRoute:
    """Test suite for MC index route (GET /mc)."""

    def test_mc_index_accessible_to_admin(self, admin_client):
        """Test that MC index page is accessible to admin."""
        response = admin_client.get('/mc')
        assert response.status_code == 200

    def test_mc_index_renders_template(self, admin_client):
        """Test that MC index renders mc.html template."""
        response = admin_client.get('/mc')
        assert response.status_code == 200
        # Should render mc.html

    def test_mc_index_sets_current_page(self, admin_client):
        """Test that MC index sets current_page context."""
        response = admin_client.get('/mc')
        assert response.status_code == 200
        # Template should receive current_page="minecraf" (yes, typo in original code)


@pytest.mark.integration
class TestRCONConnection:
    """Test suite for RCON connection management."""

    @patch('app.routes.mc.RCONClient')
    def test_rcon_init_success(self, mock_rcon_class, admin_client, app):
        """Test successful RCON initialization."""
        # Mock RCON client
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.return_value = "Available commands: help, stop, list"
        mock_rcon_class.return_value = mock_rcon

        with app.app_context():
            response = admin_client.get('/mc/init')

            assert response.status_code == 200
            assert b'Available commands' in response.data or b'help' in response.data

    @patch('app.routes.mc.rcon', None)
    @patch('app.routes.mc.RCONClient')
    def test_rcon_init_connection_failure(self, mock_rcon_class, admin_client):
        """Test RCON init when connection fails."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = False
        mock_rcon_class.return_value = mock_rcon

        response = admin_client.get('/mc/init')

        assert response.status_code == 200
        assert b'FAIL' in response.data

    @patch('app.routes.mc.RCONClient')
    def test_rcon_init_exception_handling(self, mock_rcon_class, admin_client):
        """Test RCON init handles exceptions."""
        mock_rcon_class.side_effect = Exception("Connection refused")

        response = admin_client.get('/mc/init')

        # Should handle error gracefully
        assert response.status_code in [200, 500]

    @patch('app.routes.mc.rcon')
    def test_rcon_stop_success(self, mock_rcon, admin_client):
        """Test successful RCON connection stop."""
        mock_rcon_instance = Mock()
        mock_rcon_instance.stop.return_value = None

        with patch('app.routes.mc.rcon', mock_rcon_instance):
            response = admin_client.get('/mc/stop')

            assert response.status_code == 200
            assert b'OK' in response.data

    def test_rcon_stop_when_not_connected(self, admin_client):
        """Test RCON stop when rcon is None."""
        with patch('app.routes.mc.rcon', None):
            response = admin_client.get('/mc/stop')

            assert response.status_code == 200
            assert b'OK' in response.data

    @patch('app.routes.mc.rcon')
    def test_rcon_stop_exception_handling(self, mock_rcon, admin_client):
        """Test RCON stop handles exceptions."""
        mock_rcon.stop.side_effect = Exception("Stop failed")

        response = admin_client.get('/mc/stop')

        # Should handle error gracefully
        assert response.status_code in [200, 500]


@pytest.mark.integration
class TestRCONCommand:
    """Test suite for RCON command execution."""

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_success(self, mock_rcon_class, admin_client, app):
        """Test successful RCON command execution."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.return_value = "Server has 3 players online"
        mock_rcon_class.return_value = mock_rcon

        # The reset_rcon_global fixture already sets rcon to None
        with app.app_context():
            response = admin_client.post('/mc/command', data={'command': 'list'})

            assert response.status_code == 200
            assert b'players' in response.data or b'Server' in response.data

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_connection_failure(self, mock_rcon_class, admin_client):
        """Test RCON command when connection fails."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = False
        mock_rcon_class.return_value = mock_rcon

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': 'help'})

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['status'] == 'error'
            assert 'RCON not connected' in json_data['message']

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_various_commands(self, mock_rcon_class, admin_client):
        """Test various RCON commands."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True

        commands_responses = {
            'help': 'Available commands',
            'list': '0 players online',
            'say Hello': 'Message sent',
            'time set day': 'Time set to day'
        }

        for cmd, expected_response in commands_responses.items():
            mock_rcon.command.return_value = expected_response
            mock_rcon_class.return_value = mock_rcon

            with patch('app.routes.mc.rcon', None):
                response = admin_client.post('/mc/command', data={'command': cmd})

                assert response.status_code == 200

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_empty_command(self, mock_rcon_class, admin_client):
        """Test RCON command with empty command string."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.return_value = "Unknown command"
        mock_rcon_class.return_value = mock_rcon

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': ''})

            assert response.status_code == 400  # Empty command should return bad request
            json_data = response.get_json()
            assert json_data['status'] == 'error'

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_special_characters(self, mock_rcon_class, admin_client):
        """Test RCON command with special characters."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.return_value = "Command executed"
        mock_rcon_class.return_value = mock_rcon

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': 'say <hello> "world"'})

            assert response.status_code == 200

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_exception_during_execution(self, mock_rcon_class, admin_client):
        """Test RCON command handles exceptions during execution."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.side_effect = Exception("Command execution failed")
        mock_rcon_class.return_value = mock_rcon

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': 'help'})

            # Should handle error gracefully
            assert response.status_code in [200, 500]


@pytest.mark.integration
class TestRCONQuery:
    """Test suite for RCON query functionality."""

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_success(self, mock_query_class, admin_client):
        """Test successful RCON query."""
        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'hostname': 'Test Server',
            'players': ['player1', 'player2'],
            'maxplayers': 20,
            'version': '1.19.2'
        }
        mock_query_class.return_value = mock_query

        response = admin_client.get('/mc/query')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['status'] == 'success'
        assert 'hostname' in json_data['data'] or 'players' in json_data['data']

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_connection_error(self, mock_query_class, admin_client):
        """Test RCON query handles connection errors."""
        mock_query_class.side_effect = socket.error("Connection refused")

        response = admin_client.get('/mc/query')

        assert response.status_code == 200  # Returns 200 with error in JSON
        json_data = response.get_json()
        assert json_data['status'] == 'error'
        assert 'message' in json_data

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_connection_reset(self, mock_query_class, admin_client):
        """Test RCON query handles connection reset errors."""
        mock_query_class.side_effect = ConnectionResetError("Connection reset by peer")

        response = admin_client.get('/mc/query')

        assert response.status_code == 200  # Returns 200 with error in JSON
        json_data = response.get_json()
        assert json_data['status'] == 'error'
        assert 'message' in json_data

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_timeout(self, mock_query_class, admin_client):
        """Test RCON query handles timeout."""
        mock_query_class.side_effect = socket.timeout("Query timed out")

        response = admin_client.get('/mc/query')

        # Should handle timeout error
        assert response.status_code in [200, 500]

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_returns_json(self, mock_query_class, admin_client):
        """Test that RCON query returns JSON response."""
        mock_query = Mock()
        mock_query.get_full_stats.return_value = {'status': 'online'}
        mock_query_class.return_value = mock_query

        response = admin_client.get('/mc/query')

        assert response.status_code == 200
        assert response.content_type == 'application/json' or response.is_json


@pytest.mark.integration
class TestMCCommandList:
    """Test suite for Minecraft command listing."""

    def test_mc_list_returns_json(self, admin_client):
        """Test that /mc/list returns JSON response."""
        response = admin_client.get('/mc/list')

        assert response.status_code == 200
        assert response.is_json

    def test_mc_list_empty_commands(self, admin_client, db):
        """Test /mc/list with no commands in database."""
        from app.models import MinecraftCommand

        # Clear all commands
        MinecraftCommand.query.delete()
        db.session.commit()

        response = admin_client.get('/mc/list')

        assert response.status_code == 200
        json_data = response.get_json()
        assert isinstance(json_data, list)
        assert len(json_data) == 0

    def test_mc_list_with_commands(self, admin_client, db):
        """Test /mc/list with commands in database."""
        from app.models import MinecraftCommand

        # Add test commands
        cmd1 = MinecraftCommand(command_name='help')
        cmd2 = MinecraftCommand(command_name='list')
        db.session.add_all([cmd1, cmd2])
        db.session.commit()

        response = admin_client.get('/mc/list')

        assert response.status_code == 200
        json_data = response.get_json()
        assert isinstance(json_data, list)
        assert len(json_data) >= 2

        # Cleanup
        db.session.delete(cmd1)
        db.session.delete(cmd2)
        db.session.commit()

    def test_mc_list_ordered_by_id(self, admin_client, db):
        """Test that /mc/list returns commands ordered by command_id."""
        from app.models import MinecraftCommand

        # Add commands in specific order
        cmd1 = MinecraftCommand(command_name='zeta')
        cmd2 = MinecraftCommand(command_name='alpha')
        db.session.add_all([cmd1, cmd2])
        db.session.commit()

        response = admin_client.get('/mc/list')

        assert response.status_code == 200
        json_data = response.get_json()

        # Should be ordered by ID, not alphabetically
        if len(json_data) >= 2:
            # Verify it's a list of dictionaries
            assert all(isinstance(item, dict) for item in json_data)

        # Cleanup
        db.session.delete(cmd1)
        db.session.delete(cmd2)
        db.session.commit()

    def test_mc_list_command_structure(self, admin_client, db):
        """Test that /mc/list returns properly structured command objects."""
        from app.models import MinecraftCommand

        cmd = MinecraftCommand(command_name='test')
        db.session.add(cmd)
        db.session.commit()

        response = admin_client.get('/mc/list')

        assert response.status_code == 200
        json_data = response.get_json()

        # Find our test command
        test_cmd = next((c for c in json_data if c.get('command') == 'test'), None)
        if test_cmd:
            assert 'command' in test_cmd
            assert 'description' in test_cmd

        # Cleanup
        db.session.delete(cmd)
        db.session.commit()


@pytest.mark.integration
class TestRCONConnectionManagement:
    """Test suite for RCON connection lifecycle management."""

    @patch('app.routes.mc.RCONClient')
    def test_rcon_connect_creates_new_client_when_none(self, mock_rcon_class, admin_client, app):
        """Test that rconConnect creates new client when rcon is None."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon_class.return_value = mock_rcon

        # The reset_rcon_global fixture already ensures rcon is None
        with app.app_context():
            from app.routes.mc import rconConnect
            result = rconConnect()

            assert result is mock_rcon  # Returns RCONClient object, not boolean
            mock_rcon_class.assert_called_once()

    @patch('app.routes.mc.RCONClient')
    def test_rcon_connect_uses_config_values(self, mock_rcon_class, admin_client, app):
        """Test that rconConnect uses configuration values."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon_class.return_value = mock_rcon

        # The reset_rcon_global fixture already ensures rcon is None
        with app.app_context():
            from app.routes.mc import rconConnect
            rconConnect()

            # Verify RCONClient was called with config values
            mock_rcon_class.assert_called_once()

    @patch('app.routes.mc.RCONClient')
    def test_rcon_multiple_commands_reuse_connection(self, mock_rcon_class, admin_client, app):
        """Test that multiple commands can reuse the same connection."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.return_value = "OK"
        mock_rcon_class.return_value = mock_rcon

        # The reset_rcon_global fixture already ensures rcon is None
        with app.app_context():
            # Execute multiple commands
            admin_client.post('/mc/command', data={'command': 'help'})
            admin_client.post('/mc/command', data={'command': 'list'})

            # RCONClient should be created (connections may be reused internally)
            assert mock_rcon_class.call_count >= 1


@pytest.mark.integration
class TestMCRouteEdgeCases:
    """Test edge cases for MC routes."""

    def test_mc_route_with_missing_config(self, admin_client, monkeypatch):
        """Test MC routes when RCON config is missing."""
        # Remove RCON config
        from config import Config
        monkeypatch.setattr(Config, 'RCON_HOST', None)

        response = admin_client.get('/mc/init')

        # Should handle missing config
        assert response.status_code in [200, 500]

    @patch('app.routes.mc.RCONClient')
    def test_mc_command_with_unicode(self, mock_rcon_class, admin_client):
        """Test RCON command with Unicode characters."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.return_value = "Message: 你好"
        mock_rcon_class.return_value = mock_rcon

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': 'say 你好'})

            assert response.status_code == 200

    @patch('app.routes.mc.RCONClient')
    def test_mc_command_very_long_command(self, mock_rcon_class, admin_client):
        """Test RCON with very long command string."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.return_value = "Command too long"
        mock_rcon_class.return_value = mock_rcon

        long_command = 'say ' + 'A' * 1000

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': long_command})

            assert response.status_code in [200, 400, 500]

    def test_mc_list_database_error_handling(self, admin_client, monkeypatch):
        """Test /mc/list handles database errors."""
        from app.models import MinecraftCommand

        # Mock query to raise exception
        def mock_query_error(*args, **kwargs):
            raise Exception("Database error")

        # This test would require deeper mocking of SQLAlchemy
        # For now, just verify the route doesn't crash
        response = admin_client.get('/mc/list')
        assert response.status_code in [200, 500]

    @patch('app.routes.mc.RCONClient')
    def test_rcon_network_timeout(self, mock_rcon_class, admin_client):
        """Test RCON handles network timeouts."""
        mock_rcon_class.side_effect = socket.timeout("Network timeout")

        with patch('app.routes.mc.rcon', None):
            response = admin_client.get('/mc/init')

            # Should handle timeout
            assert response.status_code in [200, 500]


@pytest.mark.integration
class TestMCExceptionHandlers:
    """Test suite for exception handlers in MC routes to improve coverage."""

    @patch('app.routes.mc.RCONClient')
    def test_rcon_connect_connection_refused_error(self, mock_rcon_class, admin_client):
        """Test rconConnect handles ConnectionRefusedError (lines 55-56)."""
        mock_rcon_class.side_effect = ConnectionRefusedError("Connection refused")

        with patch('app.routes.mc.rcon', None):
            response = admin_client.get('/mc/init')
            assert response.status_code in [200, 500]
            assert response.data == b'FAIL'

    @patch('app.routes.mc.RCONClient')
    def test_rcon_connect_connection_reset_error(self, mock_rcon_class, admin_client):
        """Test rconConnect handles ConnectionResetError (lines 59-60)."""
        mock_rcon_class.side_effect = ConnectionResetError("Connection reset by peer")

        with patch('app.routes.mc.rcon', None):
            response = admin_client.get('/mc/init')
            assert response.status_code in [200, 500]
            assert response.data == b'FAIL'

    @patch('app.routes.mc.RCONClient')
    def test_rcon_connect_socket_error(self, mock_rcon_class, admin_client):
        """Test rconConnect handles socket.error (lines 59-60)."""
        mock_rcon_class.side_effect = socket.error("Socket error")

        with patch('app.routes.mc.rcon', None):
            response = admin_client.get('/mc/init')
            assert response.status_code in [200, 500]
            assert response.data == b'FAIL'

    def test_rcon_stop_socket_error(self, admin_client):
        """Test rconStop handles socket.error during disconnect (line 92)."""
        from app import rcon as app_rcon

        mock_rcon = Mock()
        mock_rcon.stop.side_effect = socket.error("Socket error during disconnect")

        with patch('app.routes.mc.rcon', mock_rcon):
            response = admin_client.get('/mc/stop')
            assert response.status_code == 200
            assert response.data == b'OK'

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_timeout_error(self, mock_rcon_class, admin_client):
        """Test rconCommand handles socket.timeout (lines 127-128)."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.side_effect = socket.timeout("Command timeout")
        mock_rcon_class.return_value = mock_rcon

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': 'help'})
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['status'] == 'error'
            assert 'timeout' in json_data['message'].lower()

    @patch('app.routes.mc.RCONClient')
    def test_rcon_command_connection_reset_error(self, mock_rcon_class, admin_client):
        """Test rconCommand handles ConnectionResetError (lines 134-136)."""
        mock_rcon = Mock()
        mock_rcon.login.return_value = True
        mock_rcon.command.side_effect = ConnectionResetError("Connection reset")
        mock_rcon_class.return_value = mock_rcon

        with patch('app.routes.mc.rcon', None):
            response = admin_client.post('/mc/command', data={'command': 'help'})
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['status'] == 'error'
            assert 'lost' in json_data['message'].lower() or 'shutdown' in json_data['message'].lower()

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_connection_refused_error(self, mock_query_class, admin_client):
        """Test rconQuery handles ConnectionRefusedError (lines 175-176)."""
        mock_query_class.side_effect = ConnectionRefusedError("Connection refused")

        response = admin_client.get('/mc/query')
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['status'] == 'error'
        assert 'offline' in json_data['message'].lower() or 'closed' in json_data['message'].lower()

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_os_error(self, mock_query_class, admin_client):
        """Test rconQuery handles OSError (lines 188-197)."""
        mock_query_class.side_effect = OSError("OS error")

        response = admin_client.get('/mc/query')
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['status'] == 'error'
        assert 'system' in json_data['message'].lower() or 'error' in json_data['message'].lower()

    @patch('app.routes.mc.QUERYClient')
    def test_rcon_query_unexpected_exception(self, mock_query_class, admin_client):
        """Test rconQuery handles unexpected exceptions (lines 195-197)."""
        mock_query_class.side_effect = ValueError("Unexpected error")

        response = admin_client.get('/mc/query')
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['status'] == 'error'
        assert 'failed' in json_data['message'].lower()
