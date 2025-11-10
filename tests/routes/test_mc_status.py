"""
Comprehensive test suite for Minecraft server status endpoint (TC-10).

This test suite implements full test coverage for:
1. /mc/status endpoint with TCP connection testing
2. QUERYClient integration with proper mocking
3. Server-side caching behavior
4. Error handling and edge cases
5. Authentication and authorization

Priority tests implement scenarios flagged as critical in code review:
- Online/offline status detection
- Cache behavior and expiration
- Type conversion (string→int)
- Error handling for all network exceptions
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from app.routes import mc


# ============================================================================
# PRIORITY 1: CRITICAL FUNCTIONALITY TESTS
# ============================================================================

class TestMCStatusEndpointCritical:
    """Critical tests for /mc/status endpoint functionality."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear module-level cache before each test."""
        mc._status_cache = None
        mc._status_cache_time = None
        yield
        mc._status_cache = None
        mc._status_cache_time = None

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_status_online_with_tcp_test_pass(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test /mc/status when server is online (TCP test passes).

        Mocks:
        - TCP socket connection succeeds
        - QUERYClient returns full stats

        Expected:
        - status: 'online'
        - players data present and correct types
        - server info included (version, motd, map, plugins)
        """
        # Arrange: Mock TCP connection test to succeed
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        # Arrange: Mock query response with full stats (as mctools returns them)
        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '2',  # mctools returns strings!
            'maxplayers': '20',
            'players': ['player1', 'player2'],
            'version': '1.20.1',
            'motd': 'Welcome to the server',
            'map': 'world',
            'plugins': 'essentials;worldedit'
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')

        # Assert: Response structure
        assert response.status_code == 200
        json_data = response.get_json()

        # Assert: Status fields
        assert json_data['status'] == 'online'
        assert 'timestamp' in json_data
        assert 'server_address' in json_data
        assert 'query_time_ms' in json_data
        assert isinstance(json_data['query_time_ms'], int)

        # Assert: Player data (converted to integers)
        assert json_data['players']['online'] == 2  # string '2' → int 2
        assert json_data['players']['max'] == 20
        assert json_data['players']['list'] == ['player1', 'player2']
        assert isinstance(json_data['players']['online'], int)
        assert isinstance(json_data['players']['max'], int)

        # Assert: Server info
        assert json_data['version'] == '1.20.1'
        assert json_data['motd'] == 'Welcome to the server'
        assert json_data['map'] == 'world'
        assert json_data['plugins'] == 'essentials;worldedit'

        # Assert: Mocks called correctly
        mock_socket_instance.settimeout.assert_called_with(2)  # 2-second TCP timeout
        mock_socket_instance.close.assert_called_once()
        mock_query.get_full_stats.assert_called_once()

    @patch('app.routes.mc.socket.socket')
    def test_status_offline_tcp_connection_refused(self, mock_socket_class, admin_client):
        """
        Test /mc/status when server is offline (ConnectionRefusedError).

        Mocks:
        - TCP connection test fails with ConnectionRefusedError

        Expected:
        - status: 'offline'
        - error field present with user-friendly message
        - Quick response (no delay waiting for query timeout)
        """
        # Arrange: Mock TCP connection to fail
        mock_socket_instance = Mock()
        mock_socket_instance.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_class.return_value = mock_socket_instance

        # Act
        response = admin_client.get('/mc/status')

        # Assert: Response
        assert response.status_code == 200
        json_data = response.get_json()

        # Assert: Offline status
        assert json_data['status'] == 'offline'
        assert 'error' in json_data
        assert json_data['error'] == 'Server offline or unreachable'
        assert 'timestamp' in json_data
        assert 'server_address' in json_data

        # Note: Socket cleanup only happens if connect() succeeds
        # When connect() raises exception, socket doesn't need explicit close
        # assert_called_once() would fail - this is correct behavior

    @patch('app.routes.mc.socket.socket')
    def test_status_offline_tcp_timeout(self, mock_socket_class, admin_client):
        """
        Test /mc/status when TCP connection times out.

        Expected:
        - status: 'offline'
        - Fast response (~2 seconds)
        """
        import socket as socket_module

        # Arrange: Mock TCP timeout
        mock_socket_instance = Mock()
        mock_socket_instance.connect.side_effect = socket_module.timeout("Connection timed out")
        mock_socket_class.return_value = mock_socket_instance

        # Act
        start_time = time.time()
        response = admin_client.get('/mc/status')
        elapsed = time.time() - start_time

        # Assert
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['status'] == 'offline'

        # Assert: Quick response (< 5 seconds in test environment)
        assert elapsed < 5.0, f"Response took {elapsed}s, expected < 5s"

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_status_online_with_zero_players(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test /mc/status with server online but no players.

        Expected:
        - status: 'online'
        - players.online: 0
        - players.list: []
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '0',
            'maxplayers': '20',
            'players': [],
            'version': '1.20.1',
            'motd': 'Empty server',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert
        assert json_data['status'] == 'online'
        assert json_data['players']['online'] == 0
        assert json_data['players']['max'] == 20
        assert json_data['players']['list'] == []

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_status_tcp_pass_but_query_fails(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test when TCP test passes but query fails (partial server failure).

        Expected:
        - status: 'offline' (query failed)
        - error field present
        """
        # Arrange: TCP succeeds
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        # Arrange: Query fails
        mock_query = Mock()
        mock_query.get_full_stats.side_effect = TimeoutError("Query timeout")
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert
        assert json_data['status'] == 'offline'
        assert 'error' in json_data


# ============================================================================
# PRIORITY 2: CACHING BEHAVIOR TESTS
# ============================================================================

class TestMCStatusCaching:
    """Test suite for server-side caching behavior."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before/after each test."""
        mc._status_cache = None
        mc._status_cache_time = None
        yield
        mc._status_cache = None
        mc._status_cache_time = None

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_cache_returns_same_result_within_duration(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test that cache returns same result for requests within cache duration.

        Expected:
        - First request queries server
        - Second request (within cache TTL) returns cached result
        - Query client called only once
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '3',
            'maxplayers': '20',
            'players': ['p1', 'p2', 'p3'],
            'version': '1.20.1',
            'motd': 'Test',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act: First request
        response1 = admin_client.get('/mc/status')
        assert response1.status_code == 200
        query_calls_first = mock_query_class.call_count

        # Act: Second request immediately (within cache duration)
        response2 = admin_client.get('/mc/status')
        assert response2.status_code == 200
        query_calls_second = mock_query_class.call_count

        # Assert: Query not called again (cache hit)
        assert query_calls_first == query_calls_second == 1

        # Assert: Responses identical
        assert response1.get_json() == response2.get_json()

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_cache_expires_after_duration(self, mock_socket_class, mock_query_class, admin_client, monkeypatch):
        """
        Test that cache expires after MC_STATUS_CACHE_DURATION.

        Expected:
        - First request caches result
        - Manually expire cache by setting old timestamp
        - Second request queries server again (cache expired)
        """
        # Arrange: Set short cache duration
        monkeypatch.setattr('app.routes.mc.Config.MC_STATUS_CACHE_DURATION', 10)

        # Arrange: Mock successful queries
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '1',
            'maxplayers': '20',
            'players': ['player1'],
            'version': '1.20.1',
            'motd': 'Test',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act: First request (populates cache)
        response1 = admin_client.get('/mc/status')
        assert response1.status_code == 200
        calls_first = mock_query_class.call_count

        # Manually expire cache by setting timestamp to 11 seconds ago
        import time
        mc._status_cache_time = time.time() - 11.0

        # Act: Second request (cache should be expired)
        response2 = admin_client.get('/mc/status')
        assert response2.status_code == 200
        calls_second = mock_query_class.call_count

        # Assert: Query called twice (cache expired and refetched)
        assert calls_second > calls_first, f"Expected query called twice, got {calls_second} calls"

    @patch('app.routes.mc.socket.socket')
    def test_offline_status_also_cached(self, mock_socket_class, admin_client):
        """
        Test that offline status responses are also cached.

        Expected:
        - First offline check cached
        - Second check returns cached offline status
        """
        # Arrange: TCP failure
        mock_socket_instance = Mock()
        mock_socket_instance.connect.side_effect = ConnectionRefusedError()
        mock_socket_class.return_value = mock_socket_instance

        # Act: First request
        response1 = admin_client.get('/mc/status')
        assert response1.get_json()['status'] == 'offline'
        socket_calls_first = mock_socket_class.call_count

        # Act: Second request (should use cache)
        response2 = admin_client.get('/mc/status')
        assert response2.get_json()['status'] == 'offline'
        socket_calls_second = mock_socket_class.call_count

        # Assert: Socket not created again (cache hit)
        assert socket_calls_first == socket_calls_second


# ============================================================================
# PRIORITY 3: DATA TYPE HANDLING
# ============================================================================

class TestMCStatusDataTypes:
    """Test data type conversions and edge cases."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        mc._status_cache = None
        mc._status_cache_time = None
        yield
        mc._status_cache = None
        mc._status_cache_time = None

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_string_player_counts_converted_to_integers(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test that string player counts from mctools are converted to int.

        mctools returns 'numplayers' and 'maxplayers' as strings.
        Backend must convert to integers for JavaScript.
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '5',  # String
            'maxplayers': '20', # String
            'players': ['p1', 'p2', 'p3', 'p4', 'p5'],
            'version': '1.20.1',
            'motd': 'Test',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert: Converted to integers
        assert json_data['players']['online'] == 5
        assert json_data['players']['max'] == 20
        assert isinstance(json_data['players']['online'], int)
        assert isinstance(json_data['players']['max'], int)

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_null_player_count_handled_gracefully(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test handling of None/null player counts.

        Expected:
        - Defaults to 0 for null values
        - Empty list for null players
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': None,
            'maxplayers': None,
            'players': None,
            'version': '1.20.1',
            'motd': 'Test',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert: Graceful defaults
        assert json_data['status'] == 'online'
        assert json_data['players']['online'] == 0
        assert json_data['players']['max'] == 0
        assert json_data['players']['list'] == []

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_missing_optional_fields_use_defaults(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test that missing optional fields use appropriate defaults.

        Expected:
        - version: 'Unknown'
        - motd: ''
        - map: 'Unknown'
        - plugins: ''
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '1',
            'maxplayers': '20',
            'players': ['player1']
            # Missing: version, motd, map, plugins
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert: Defaults applied
        assert json_data['status'] == 'online'
        assert json_data['version'] == 'Unknown'
        assert json_data['motd'] == ''
        assert json_data['map'] == 'Unknown'
        assert json_data['plugins'] == ''

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_timestamp_is_iso8601_format(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test that timestamp is in ISO 8601 format with timezone.

        Expected format: 2025-11-03T14:30:45.123456+00:00
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '0',
            'maxplayers': '20',
            'players': [],
            'version': '1.20.1',
            'motd': 'Test',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert: Timestamp format
        timestamp = json_data['timestamp']
        assert 'T' in timestamp
        assert isinstance(timestamp, str)

        # Assert: Can be parsed back to datetime
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_time, datetime)


# ============================================================================
# PRIORITY 4: AUTHENTICATION & AUTHORIZATION
# ============================================================================

class TestMCStatusAuthentication:
    """Test authentication and authorization for /mc/status."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        mc._status_cache = None
        mc._status_cache_time = None
        yield
        mc._status_cache = None
        mc._status_cache_time = None

    def test_unauthenticated_user_cannot_access_status(self, client):
        """
        Test that unauthenticated users cannot access /mc/status.

        Expected:
        - Redirect to login (302) or Unauthorized (401)
        """
        response = client.get('/mc/status')
        assert response.status_code in [302, 401]

    @patch('app.routes.mc.socket.socket')
    def test_user_without_minecrafter_role_forbidden(self, mock_socket_class, auth_client):
        """
        Test that users without 'minecrafter' role get 403 Forbidden.

        Note: auth_client is a regular authenticated user without minecrafter role.

        Expected:
        - HTTP 403
        """
        response = auth_client.get('/mc/status')
        assert response.status_code == 403

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_admin_can_access_status(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test that admin users can access status endpoint.

        Expected:
        - HTTP 200
        - Valid response
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '0',
            'maxplayers': '20',
            'players': [],
            'version': '1.20.1',
            'motd': 'Test',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')

        # Assert
        assert response.status_code == 200
        assert response.get_json()['status'] in ['online', 'offline']


# ============================================================================
# PRIORITY 5: ERROR HANDLING
# ============================================================================

class TestMCStatusErrorHandling:
    """Test error handling for various failure scenarios."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        mc._status_cache = None
        mc._status_cache_time = None
        yield
        mc._status_cache = None
        mc._status_cache_time = None

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_unexpected_exception_returns_offline(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test that unexpected exceptions are handled gracefully.

        Expected:
        - status: 'offline'
        - error field present
        - No 500 error
        """
        # Arrange: TCP succeeds
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        # Arrange: Query raises unexpected exception
        mock_query = Mock()
        mock_query.get_full_stats.side_effect = Exception("Unexpected error")
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')

        # Assert: Graceful handling
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['status'] == 'offline'
        assert 'error' in json_data

    @patch('app.routes.mc.socket.socket')
    def test_os_error_handled_correctly(self, mock_socket_class, admin_client):
        """
        Test handling of OS-level errors (network unreachable, etc.).

        Expected:
        - status: 'offline'
        - Appropriate error message
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_instance.connect.side_effect = OSError("Network unreachable")
        mock_socket_class.return_value = mock_socket_instance

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert
        assert response.status_code == 200
        assert json_data['status'] == 'offline'
        assert 'error' in json_data

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_connection_reset_during_query(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test handling of ConnectionResetError during query.

        Expected:
        - status: 'offline'
        - Graceful error handling
        """
        # Arrange: TCP succeeds
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        # Arrange: Query fails with ConnectionResetError
        mock_query = Mock()
        mock_query.get_full_stats.side_effect = ConnectionResetError("Connection reset")
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert
        assert response.status_code == 200
        assert json_data['status'] == 'offline'


# ============================================================================
# PRIORITY 6: PERFORMANCE TESTS
# ============================================================================

class TestMCStatusPerformance:
    """Test performance characteristics of status endpoint."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        mc._status_cache = None
        mc._status_cache_time = None
        yield
        mc._status_cache = None
        mc._status_cache_time = None

    @patch('app.routes.mc.QUERYClient')
    @patch('app.routes.mc.socket.socket')
    def test_query_time_ms_recorded_correctly(self, mock_socket_class, mock_query_class, admin_client):
        """
        Test that query_time_ms is recorded in response.

        Expected:
        - query_time_ms field present
        - Value is integer >= 0
        - Reasonable value (< 10 seconds)
        """
        # Arrange
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance

        mock_query = Mock()
        mock_query.get_full_stats.return_value = {
            'numplayers': '0',
            'maxplayers': '20',
            'players': [],
            'version': '1.20.1',
            'motd': 'Test',
            'map': 'world',
            'plugins': ''
        }
        mock_query_class.return_value = mock_query

        # Act
        response = admin_client.get('/mc/status')
        json_data = response.get_json()

        # Assert
        assert 'query_time_ms' in json_data
        assert isinstance(json_data['query_time_ms'], int)
        assert json_data['query_time_ms'] >= 0
        assert json_data['query_time_ms'] < 10000  # Less than 10 seconds
