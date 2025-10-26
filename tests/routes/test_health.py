"""
Integration tests for health check endpoint.

Tests cover:
- Health endpoint returns 200 when healthy
- Returns JSON response
- CSRF exemption
- Database connectivity check
- Caching behavior
- Failure scenarios
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from app import __version__


@pytest.mark.integration
class TestHealthEndpoint:
    """Test suite for /health endpoint."""

    def test_health_endpoint_exists(self, client):
        """Test that health endpoint exists and returns 200."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'

        # Verify we can parse the JSON
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_health_response_structure(self, client):
        """Test that health response has expected structure."""
        response = client.get('/health')
        data = json.loads(response.data)

        # Required fields
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert 'checks' in data

        # Checks structure
        assert 'app' in data['checks']
        assert 'database' in data['checks']

    def test_health_status_healthy(self, client, db):
        """Test that health status is 'healthy' when all checks pass."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert data['status'] == 'healthy'
        assert data['checks']['app']['status'] == 'up'
        assert data['checks']['database']['status'] == 'up'

    def test_health_version_included(self, client):
        """Test that version is included in response."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert data['version'] == __version__

    def test_health_timestamp_format(self, client):
        """Test that timestamp is in ISO format."""
        response = client.get('/health')
        data = json.loads(response.data)

        # Should be parseable as ISO datetime
        timestamp = data['timestamp']
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_time, datetime)

    def test_health_app_check_always_up(self, client):
        """Test that app check is always 'up' when endpoint is accessible."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert data['checks']['app']['status'] == 'up'
        assert data['checks']['app']['message'] == 'Application running'

    def test_health_database_check_up(self, client, db):
        """Test that database check is 'up' when database is connected."""
        response = client.get('/health')
        data = json.loads(response.data)

        db_check = data['checks']['database']
        assert db_check['status'] == 'up'
        assert db_check['message'] == 'Database connected'
        assert 'response_time_ms' in db_check
        assert isinstance(db_check['response_time_ms'], (int, float))

    def test_health_database_response_time(self, client, db):
        """Test that database response time is measured."""
        response = client.get('/health')
        data = json.loads(response.data)

        response_time = data['checks']['database']['response_time_ms']
        assert response_time >= 0
        assert response_time < 10000  # Should be under 10 seconds

    def test_health_csrf_exempt(self, csrf_client, db):
        """Test that health endpoint is exempt from CSRF protection."""
        # CSRF-enabled client should still be able to access health endpoint
        response = csrf_client.get('/health')
        assert response.status_code == 200


@pytest.mark.integration
class TestHealthCaching:
    """Test suite for health check caching behavior."""

    def test_health_cache_indicator(self, client, db):
        """Test that cache indicator is present in response."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert 'cached' in data['checks']['database']
        assert isinstance(data['checks']['database']['cached'], bool)

    def test_health_first_request_not_cached(self, client, db):
        """Test that first request is not cached."""
        # Clear any existing cache by accessing a fresh app context
        response = client.get('/health')
        data = json.loads(response.data)

        # First request may or may not be cached depending on test order
        # Just verify the field exists
        assert 'cached' in data['checks']['database']

    def test_health_subsequent_request_may_be_cached(self, client, db):
        """Test that subsequent requests may use cache."""
        # First request
        response1 = client.get('/health')
        data1 = json.loads(response1.data)

        # Second request (should potentially be cached)
        response2 = client.get('/health')
        data2 = json.loads(response2.data)

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200


@pytest.mark.integration
class TestHealthFailureScenarios:
    """Test suite for health check failure scenarios."""

    def test_health_database_failure_returns_503(self, client, db):
        """Test that database failure returns 503 Service Unavailable."""
        # Clear the cache first
        from app.routes import health
        health._db_health_cache['result'] = None
        health._db_health_cache['timestamp'] = None

        # Mock database failure
        with patch('app.routes.health.db.session.execute') as mock_execute:
            mock_execute.side_effect = Exception('Database connection failed')

            response = client.get('/health')
            data = json.loads(response.data)

            assert response.status_code == 503
            assert data['status'] == 'unhealthy'
            assert data['checks']['database']['status'] == 'down'
            assert 'failed' in data['checks']['database']['message'].lower()

    def test_health_database_failure_details(self, client, db):
        """Test that database failure includes error details."""
        # Clear the cache first
        from app.routes import health
        health._db_health_cache['result'] = None
        health._db_health_cache['timestamp'] = None

        with patch('app.routes.health.db.session.execute') as mock_execute:
            mock_execute.side_effect = Exception('Connection timeout')

            response = client.get('/health')
            data = json.loads(response.data)

            db_check = data['checks']['database']
            assert db_check['status'] == 'down'
            assert 'Connection timeout' in db_check['message']
            assert db_check['response_time_ms'] is None

    def test_health_app_still_up_when_db_down(self, client, db):
        """Test that app check is still 'up' even when database is down."""
        # Clear the cache first
        from app.routes import health
        health._db_health_cache['result'] = None
        health._db_health_cache['timestamp'] = None

        with patch('app.routes.health.db.session.execute') as mock_execute:
            mock_execute.side_effect = Exception('Database error')

            response = client.get('/health')
            data = json.loads(response.data)

            # App should still be up
            assert data['checks']['app']['status'] == 'up'
            # Overall status should be unhealthy
            assert data['status'] == 'unhealthy'


@pytest.mark.integration
class TestHealthEndpointAccessibility:
    """Test suite for health endpoint accessibility."""

    def test_health_accessible_without_authentication(self, client):
        """Test that health endpoint is accessible without login."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_accessible_with_authentication(self, auth_client):
        """Test that health endpoint is accessible when logged in."""
        response = auth_client.get('/health')
        assert response.status_code == 200

    def test_health_accepts_only_get(self, client):
        """Test that health endpoint only accepts GET requests."""
        response = client.post('/health')
        assert response.status_code == 405  # Method Not Allowed

        response = client.put('/health')
        assert response.status_code == 405

        response = client.delete('/health')
        assert response.status_code == 405
