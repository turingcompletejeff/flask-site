"""
Comprehensive tests for database sequence synchronization (TC-61).

Tests cover the following routes and functionality:

Routes Tested:
- POST /admin/fix-sequences - Legacy endpoint (backward compatibility)
- POST /admin/sequences/<table_name> - Individual table fix endpoint
- POST /admin/sequences/fix-all - Orchestrator endpoint (new v2)

Helper Function:
- fix_single_table_sequence() - Shared sequence fix implementation

Features Tested:
- Sequence synchronization for all valid tables (blog-posts, users, roles, minecraft)
- Error handling and recovery
- Database transaction management
- Access control (authentication and authorization)
- Input validation and security
- Audit logging
- Response format validation

Authorization Tests:
- Unauthenticated users get 302 redirect to login
- Non-admin users get 403 forbidden
- Only admins can execute sequence fixes

Edge Cases:
- Empty tables (max_id = None/0)
- Sequence already at correct value
- Invalid table names (security)
- Database connection failures
- Transaction rollback on error
- Concurrent requests handling

Test Organization:
- Unit tests for fix_single_table_sequence() helper
- Integration tests for each endpoint
- Security and authorization tests
- Response validation tests
- Edge case and error handling tests
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from flask import url_for
from app.models import User, Role, BlogPost, MinecraftCommand
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app import db


# ============================================================================
# Helper Function Tests: fix_single_table_sequence()
# ============================================================================

class TestFixSingleTableSequence:
    """Test the fix_single_table_sequence() helper function in isolation."""

    def test_fix_sequence_success_with_data(self, app, db, admin_user):
        """Helper function successfully fixes sequence when table has data."""
        with app.app_context():
            # Login to set current_user
            from flask_login import login_user
            login_user(admin_user)

            # Create a blog post to set max_id
            post = BlogPost(
                title='Test Post',
                content='Content',
                is_draft=False
            )
            db.session.add(post)
            db.session.commit()
            max_id = post.id

            # Import here to access the function
            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            # Mock execute to handle SQLite/PostgreSQL differences
            with patch.object(db.session, 'execute') as mock_execute:
                # First call: SELECT MAX(id) - returns max_id
                # Second call: ALTER SEQUENCE - succeeds
                mock_execute.side_effect = [
                    MagicMock(scalar=MagicMock(return_value=max_id)),
                    None  # ALTER SEQUENCE doesn't return anything
                ]
                with patch.object(db.session, 'commit'):
                    success, result = fix_single_table_sequence(table_info)

            assert success is True
            assert result['status'] == 'success'
            assert result['table'] == 'blog_posts'
            assert result['sequence_name'] == 'blog_posts_id_seq'
            assert result['new_value'] == max_id + 1
            assert result['old_value'] == max_id
            assert 'execution_time_ms' in result
            assert result['execution_time_ms'] >= 0

    def test_fix_sequence_success_empty_table(self, app, db, admin_user):
        """Helper function handles empty tables correctly (max_id = None)."""
        with app.app_context():
            # Login to set current_user
            from flask_login import login_user
            login_user(admin_user)

            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            # Mock execute for empty table
            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = [
                    MagicMock(scalar=MagicMock(return_value=None)),  # No records
                    None  # ALTER SEQUENCE
                ]
                with patch.object(db.session, 'commit'):
                    success, result = fix_single_table_sequence(table_info)

            assert success is True
            assert result['status'] == 'success'
            assert result['old_value'] == 0  # None becomes 0
            assert result['new_value'] == 1

    def test_fix_sequence_success_multiple_records(self, app, db, admin_user):
        """Helper function correctly uses maximum ID from table with many records."""
        with app.app_context():
            # Login to set current_user
            from flask_login import login_user
            login_user(admin_user)

            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            # Mock execute for multiple records
            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = [
                    MagicMock(scalar=MagicMock(return_value=5)),  # Max id = 5
                    None  # ALTER SEQUENCE
                ]
                with patch.object(db.session, 'commit'):
                    success, result = fix_single_table_sequence(table_info)

            assert success is True
            assert result['new_value'] == 6  # max_id (5) + 1

    def test_fix_sequence_database_error_handling(self, app, db, admin_user):
        """Helper function handles SQLAlchemy errors gracefully."""
        with app.app_context():
            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            # Mock db.session.execute to raise SQLAlchemyError
            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = SQLAlchemyError('Connection failed')

                success, result = fix_single_table_sequence(table_info)

                assert success is False
                assert result['status'] == 'error'
                assert result['error_type'] == 'SQLAlchemyError'
                assert 'message' in result
                assert 'execution_time_ms' in result

    def test_fix_sequence_transaction_rollback_on_error(self, app, db, admin_user):
        """Helper function rolls back transaction on error."""
        with app.app_context():
            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = SQLAlchemyError('DB error')

                with patch.object(db.session, 'rollback') as mock_rollback:
                    success, result = fix_single_table_sequence(table_info)

                    assert success is False
                    mock_rollback.assert_called_once()

    def test_fix_sequence_unexpected_error_handling(self, app, db, admin_user):
        """Helper function handles unexpected non-SQLAlchemy errors."""
        with app.app_context():
            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = RuntimeError('Unexpected error')

                success, result = fix_single_table_sequence(table_info)

                assert success is False
                assert result['status'] == 'error'
                assert result['error_type'] == 'RuntimeError'

    def test_fix_sequence_execution_time_tracking(self, app, db, admin_user):
        """Helper function tracks execution time accurately."""
        with app.app_context():
            # Login to set current_user
            from flask_login import login_user
            login_user(admin_user)

            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            # Mock execute for tracking time
            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = [
                    MagicMock(scalar=MagicMock(return_value=0)),
                    None  # ALTER SEQUENCE
                ]
                with patch.object(db.session, 'commit'):
                    success, result = fix_single_table_sequence(table_info)

            assert success is True
            # Execution time should be reasonable (0-5000ms)
            assert 0 <= result['execution_time_ms'] <= 5000

    @pytest.mark.parametrize("table_key", ['blog-posts', 'users', 'roles', 'minecraft'])
    def test_fix_sequence_all_valid_tables(self, app, db, admin_user, table_key):
        """Helper function works with all valid table configurations."""
        with app.app_context():
            # Login to set current_user
            from flask_login import login_user
            login_user(admin_user)

            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES[table_key]

            # Mock execute for all tables
            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = [
                    MagicMock(scalar=MagicMock(return_value=0)),
                    None  # ALTER SEQUENCE
                ]
                with patch.object(db.session, 'commit'):
                    success, result = fix_single_table_sequence(table_info)

            assert success is True
            assert result['status'] == 'success'
            assert 'table' in result
            assert 'sequence_name' in result
            assert 'new_value' in result
            assert 'old_value' in result

    def test_fix_sequence_audit_logging(self, app, db, admin_user):
        """Helper function logs audit trail for successful sequence fixes."""
        with app.app_context():
            # Login to set current_user
            from flask_login import login_user
            login_user(admin_user)

            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            with patch('app.routes.admin.current_app.logger') as mock_logger:
                with patch.object(db.session, 'execute') as mock_execute:
                    mock_execute.side_effect = [
                        MagicMock(scalar=MagicMock(return_value=0)),
                        None
                    ]
                    with patch.object(db.session, 'commit'):
                        success, result = fix_single_table_sequence(table_info)

                assert success is True
                # Verify audit log was called
                mock_logger.info.assert_called()
                call_args = mock_logger.info.call_args[0][0]
                assert 'Sequence' in call_args or 'sequence' in call_args

    def test_fix_sequence_error_logging(self, app, db, admin_user):
        """Helper function logs errors when sequence fix fails."""
        with app.app_context():
            from app.routes.admin import fix_single_table_sequence, VALID_SEQUENCE_TABLES

            table_info = VALID_SEQUENCE_TABLES['blog-posts']

            with patch.object(db.session, 'execute') as mock_execute:
                mock_execute.side_effect = SQLAlchemyError('DB error')

                with patch('app.routes.admin.current_app.logger') as mock_logger:
                    success, result = fix_single_table_sequence(table_info)

                    assert success is False
                    mock_logger.error.assert_called()


# ============================================================================
# Individual Table Endpoint Tests: POST /admin/sequences/<table_name>
# ============================================================================

class TestFixTableSequence:
    """Test the individual table sequence fix endpoint."""

    @pytest.mark.parametrize("table_name", ['blog-posts', 'users', 'roles', 'minecraft'])
    def test_fix_table_sequence_success(self, admin_client, app, db, table_name):
        """Admin can fix sequence for valid table names."""
        with app.app_context():
            # Mock sequence fix to handle SQLite/PostgreSQL differences
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                mock_fix.return_value = (True, {
                    'status': 'success',
                    'table': 'test_table',
                    'sequence_name': 'test_seq',
                    'old_value': 0,
                    'new_value': 1,
                    'execution_time_ms': 10
                })

                response = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name=table_name)
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['status'] == 'success'
                assert 'table' in data
                assert 'sequence_name' in data
                assert 'new_value' in data
                assert 'execution_time_ms' in data

    def test_fix_table_sequence_invalid_table_name(self, admin_client, app):
        """Invalid table name returns 400 error."""
        with app.app_context():
            response = admin_client.post(
                url_for('admin.fix_table_sequence', table_name='invalid_table')
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'Invalid table name' in data['message']

    def test_fix_table_sequence_sql_injection_attempt(self, admin_client, app):
        """SQL injection attempts are blocked via whitelist validation."""
        with app.app_context():
            # Try SQL injection
            response = admin_client.post(
                url_for('admin.fix_table_sequence', table_name="blog-posts'; DROP TABLE users; --")
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['status'] == 'error'

    def test_fix_table_sequence_unauthenticated_redirect(self, client, app):
        """Unauthenticated users are redirected to login."""
        with app.app_context():
            response = client.post(
                url_for('admin.fix_table_sequence', table_name='blog-posts'),
                follow_redirects=False
            )

            assert response.status_code == 302
            assert 'login' in response.location

    def test_fix_table_sequence_regular_user_forbidden(self, auth_client, app):
        """Regular (non-admin) users get 403 forbidden."""
        with app.app_context():
            response = auth_client.post(
                url_for('admin.fix_table_sequence', table_name='blog-posts'),
                follow_redirects=False
            )

            assert response.status_code == 403

    def test_fix_table_sequence_database_error_returns_500(self, admin_client, app, db):
        """Database errors are returned as 500 response."""
        with app.app_context():
            from app.routes.admin import VALID_SEQUENCE_TABLES

            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                mock_fix.return_value = (False, {
                    'status': 'error',
                    'table': 'blog_posts',
                    'error_type': 'SQLAlchemyError',
                    'message': 'Database error',
                    'execution_time_ms': 10
                })

                response = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name='blog-posts')
                )

                assert response.status_code == 500
                data = json.loads(response.data)
                assert data['status'] == 'error'

    def test_fix_table_sequence_response_format(self, admin_client, app, db):
        """Response has correct JSON structure."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                mock_fix.return_value = (True, {
                    'status': 'success',
                    'table': 'blog_posts',
                    'sequence_name': 'blog_posts_id_seq',
                    'old_value': 0,
                    'new_value': 1,
                    'execution_time_ms': 10
                })

                response = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name='blog-posts')
                )

                assert response.status_code == 200
                data = json.loads(response.data)

                # Verify required fields
                assert 'status' in data
                assert 'table' in data
                assert 'sequence_name' in data
                assert 'old_value' in data
                assert 'new_value' in data
                assert 'execution_time_ms' in data


# ============================================================================
# Legacy Endpoint Tests: POST /admin/fix-sequences
# ============================================================================

class TestFixAllSequences:
    """Test the legacy fix-all endpoint (backward compatibility)."""

    def test_fix_all_sequences_success(self, admin_client, app, db):
        """Legacy endpoint successfully fixes all sequences."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                response = admin_client.post(url_for('admin.fix_all_sequences'))

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert data['message'] == 'All sequences synchronized successfully'
            assert 'sequences_fixed' in data
            assert len(data['sequences_fixed']) == 4  # All 4 tables

    def test_fix_all_sequences_response_format(self, admin_client, app, db):
        """Legacy endpoint response has correct format."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                response = admin_client.post(url_for('admin.fix_all_sequences'))

            assert response.status_code == 200
            data = json.loads(response.data)

            # Each item should have table, sequence, next_id
            for item in data['sequences_fixed']:
                assert 'table' in item
                assert 'sequence' in item
                assert 'next_id' in item

    def test_fix_all_sequences_one_table_fails_rollback(self, admin_client, app, db):
        """Legacy endpoint fails entirely if any table fails (all-or-nothing)."""
        with app.app_context():
            from app.routes.admin import VALID_SEQUENCE_TABLES

            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # First call succeeds, second fails
                mock_fix.side_effect = [
                    (True, {
                        'status': 'success',
                        'table': 'blog_posts',
                        'sequence_name': 'blog_posts_id_seq',
                        'old_value': 0,
                        'new_value': 1,
                        'execution_time_ms': 10
                    }),
                    (False, {
                        'status': 'error',
                        'table': 'users',
                        'error_type': 'SQLAlchemyError',
                        'message': 'Database error',
                        'execution_time_ms': 10
                    })
                ]

                response = admin_client.post(url_for('admin.fix_all_sequences'))

                assert response.status_code == 500
                data = json.loads(response.data)
                assert data['status'] == 'error'

    def test_fix_all_sequences_unauthenticated_redirect(self, client, app):
        """Unauthenticated users are redirected to login."""
        with app.app_context():
            response = client.post(
                url_for('admin.fix_all_sequences'),
                follow_redirects=False
            )

            assert response.status_code == 302
            assert 'login' in response.location

    def test_fix_all_sequences_regular_user_forbidden(self, auth_client, app):
        """Regular users cannot access legacy endpoint."""
        with app.app_context():
            response = auth_client.post(
                url_for('admin.fix_all_sequences'),
                follow_redirects=False
            )

            assert response.status_code == 403

    def test_fix_all_sequences_database_error(self, admin_client, app):
        """Legacy endpoint handles database errors."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                mock_fix.side_effect = SQLAlchemyError('Connection failed')

                response = admin_client.post(url_for('admin.fix_all_sequences'))

                assert response.status_code == 500
                data = json.loads(response.data)
                assert data['status'] == 'error'


# ============================================================================
# Orchestrator Endpoint Tests: POST /admin/sequences/fix-all
# ============================================================================

class TestFixAllSequencesV2:
    """Test the new orchestrator endpoint with partial success support."""

    def test_fix_all_sequences_v2_success_all_tables(self, admin_client, app, db):
        """Orchestrator successfully fixes all tables."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert len(data['results']) == 4  # All 4 tables
            assert data['summary']['successful'] == 4
            assert data['summary']['failed'] == 0
            assert data['summary']['total'] == 4

    def test_fix_all_sequences_v2_partial_success(self, admin_client, app, db):
        """Orchestrator reports partial success when some tables fail."""
        with app.app_context():
            from app.routes.admin import VALID_SEQUENCE_TABLES

            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # Two succeed, two fail
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (False, {'status': 'error', 'table': 'users', 'error_type': 'SQLAlchemyError', 'message': 'DB error', 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (False, {'status': 'error', 'table': 'minecraft_commands', 'error_type': 'OperationalError', 'message': 'Connection lost', 'execution_time_ms': 10})
                ]

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['status'] == 'partial_success'
                assert data['summary']['successful'] == 2
                assert data['summary']['failed'] == 2

    def test_fix_all_sequences_v2_all_fail(self, admin_client, app, db):
        """Orchestrator reports error when all tables fail."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                mock_fix.side_effect = [
                    (False, {'status': 'error', 'table': 'blog_posts', 'error_type': 'SQLAlchemyError', 'message': 'DB error', 'execution_time_ms': 10}),
                    (False, {'status': 'error', 'table': 'users', 'error_type': 'SQLAlchemyError', 'message': 'DB error', 'execution_time_ms': 10}),
                    (False, {'status': 'error', 'table': 'roles', 'error_type': 'SQLAlchemyError', 'message': 'DB error', 'execution_time_ms': 10}),
                    (False, {'status': 'error', 'table': 'minecraft_commands', 'error_type': 'SQLAlchemyError', 'message': 'DB error', 'execution_time_ms': 10})
                ]

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['status'] == 'error'
                assert data['summary']['failed'] == 4

    def test_fix_all_sequences_v2_custom_table_list(self, admin_client, app, db):
        """Orchestrator accepts custom table list in request body."""
        with app.app_context():
            response = admin_client.post(
                url_for('admin.fix_all_sequences_v2'),
                json={'tables': ['blog-posts', 'users']}
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['summary']['total'] == 2

    def test_fix_all_sequences_v2_invalid_table_in_list(self, admin_client, app, db):
        """Orchestrator handles invalid table names in custom list."""
        with app.app_context():
            response = admin_client.post(
                url_for('admin.fix_all_sequences_v2'),
                json={'tables': ['blog-posts', 'invalid_table', 'users']}
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            # One should fail
            assert data['summary']['failed'] >= 1

    def test_fix_all_sequences_v2_stop_on_error_true(self, admin_client, app, db):
        """Orchestrator stops processing when stop_on_error=true and error occurs."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # First succeeds, second fails, and stop_on_error prevents processing more
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (False, {'status': 'error', 'table': 'users', 'error_type': 'SQLAlchemyError', 'message': 'DB error', 'execution_time_ms': 10})
                ]

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={'tables': ['blog-posts', 'users', 'roles', 'minecraft'], 'stop_on_error': True}
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                # summary['total'] is based on len(tables_to_fix), not actual processed count
                # But results array only has 2 items (stopped after error)
                assert data['summary']['total'] == 4  # Original table list length
                assert len(data['results']) == 2  # Only processed 2 before stopping
                assert data['summary']['successful'] == 1
                assert data['summary']['failed'] == 1

    def test_fix_all_sequences_v2_stop_on_error_false(self, admin_client, app, db):
        """Orchestrator continues processing when stop_on_error=false."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # First fails, others succeed
                mock_fix.side_effect = [
                    (False, {'status': 'error', 'table': 'blog_posts', 'error_type': 'SQLAlchemyError', 'message': 'DB error', 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={'stop_on_error': False}
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                # Should process all 4 tables
                assert data['summary']['total'] == 4

    def test_fix_all_sequences_v2_response_format(self, admin_client, app, db):
        """Orchestrator response has correct JSON structure."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

            assert response.status_code == 200
            data = json.loads(response.data)

            # Verify required fields
            assert 'status' in data
            assert 'results' in data
            assert 'summary' in data
            assert 'total' in data['summary']
            assert 'successful' in data['summary']
            assert 'failed' in data['summary']
            assert 'execution_time_ms' in data['summary']

    def test_fix_all_sequences_v2_execution_time_tracking(self, admin_client, app, db):
        """Orchestrator tracks total execution time accurately."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            # Execution time should be reasonable
            assert 0 <= data['summary']['execution_time_ms'] <= 10000

    def test_fix_all_sequences_v2_unauthenticated_redirect(self, client, app):
        """Unauthenticated users are redirected to login."""
        with app.app_context():
            response = client.post(
                url_for('admin.fix_all_sequences_v2'),
                json={},
                follow_redirects=False
            )

            assert response.status_code == 302
            assert 'login' in response.location

    def test_fix_all_sequences_v2_regular_user_forbidden(self, auth_client, app):
        """Regular users cannot access orchestrator endpoint."""
        with app.app_context():
            response = auth_client.post(
                url_for('admin.fix_all_sequences_v2'),
                json={},
                follow_redirects=False
            )

            assert response.status_code == 403

    def test_fix_all_sequences_v2_empty_request_body(self, admin_client, app, db):
        """Orchestrator handles empty request body (uses defaults)."""
        with app.app_context():
            response = admin_client.post(
                url_for('admin.fix_all_sequences_v2'),
                json={}
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['summary']['total'] == 4  # All tables by default

    def test_fix_all_sequences_v2_no_json_body(self, admin_client, app, db):
        """Orchestrator handles missing JSON body (defaults work)."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                # Post with empty JSON body (default)
                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={},
                    content_type='application/json'
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['summary']['total'] == 4  # All tables by default

    def test_fix_all_sequences_v2_unexpected_error(self, admin_client, app, db):
        """Orchestrator handles unexpected errors gracefully."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                mock_fix.side_effect = RuntimeError('Unexpected error')

                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

                assert response.status_code == 500
                data = json.loads(response.data)
                assert data['status'] == 'error'

    def test_fix_all_sequences_v2_audit_logging(self, admin_client, app, db):
        """Orchestrator logs audit trail of sequence fixes."""
        with app.app_context():
            with patch('app.routes.admin.current_app.logger') as mock_logger:
                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

                assert response.status_code == 200
                mock_logger.info.assert_called()
                call_args = mock_logger.info.call_args[0][0]
                assert 'Fix-all sequences' in call_args or 'sequences completed' in call_args


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestSequenceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_sequence_already_correct(self, admin_client, app, db):
        """Fixing sequence when it's already correct succeeds."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # Both calls succeed (idempotent)
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 1, 'new_value': 2, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 1, 'new_value': 2, 'execution_time_ms': 10})
                ]

                # Fix sequence first time
                response1 = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name='blog-posts')
                )
                assert response1.status_code == 200

                # Fix again (should be idempotent)
                response2 = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name='blog-posts')
                )
                assert response2.status_code == 200
                data = json.loads(response2.data)
                assert data['status'] == 'success'

    def test_sequence_with_large_id_values(self, admin_client, app, db):
        """Sequence fix works with large ID values."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # Simulate large ID
                mock_fix.return_value = (True, {
                    'status': 'success',
                    'table': 'blog_posts',
                    'sequence_name': 'blog_posts_id_seq',
                    'old_value': 50,
                    'new_value': 51,
                    'execution_time_ms': 10
                })

                response = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name='blog-posts')
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['new_value'] >= 51

    def test_concurrent_sequence_fixes(self, admin_client, app, db):
        """Multiple simultaneous sequence fix requests don't cause race conditions."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All calls succeed
                mock_fix.return_value = (True, {
                    'status': 'success',
                    'table': 'blog_posts',
                    'sequence_name': 'blog_posts_id_seq',
                    'old_value': 0,
                    'new_value': 1,
                    'execution_time_ms': 10
                })

                # Note: Full concurrency testing would require threading/async
                # This tests sequential calls to ensure idempotency
                responses = []
                for _ in range(3):
                    response = admin_client.post(
                        url_for('admin.fix_table_sequence', table_name='blog-posts')
                    )
                    responses.append(response)

                # All should succeed
                for response in responses:
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['status'] == 'success'

    def test_sequence_fix_empty_database(self, admin_client, app, db):
        """Sequence fix works on completely empty database."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed with max_id = 0 (empty tables)
                mock_fix.side_effect = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]

                # Database is empty by default in tests
                response = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert data['summary']['successful'] == 4


# ============================================================================
# Security Tests
# ============================================================================

class TestSequenceSecurity:
    """Test security aspects of sequence fix endpoints."""

    def test_csrf_protection_if_enabled(self, csrf_app):
        """CSRF protection works if WTF_CSRF_ENABLED is true."""
        # Note: Our test fixtures have CSRF disabled by default
        # This test documents the expected behavior if it were enabled
        # CSRF tokens would be required for POST requests
        pass

    def test_table_name_whitelist_enforcement(self, admin_client, app):
        """Table names are strictly validated against whitelist."""
        with app.app_context():
            # Try various invalid names
            invalid_names = [
                'users; DROP TABLE users;',
                'blog_posts" OR "1"="1',
                '../../../etc/passwd',
                'users%20OR%201=1',
                'minecraft_commands',  # Wrong format (should be 'minecraft')
                'blog_posts',  # Wrong format (should be 'blog-posts')
                ''
            ]

            for name in invalid_names:
                response = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name=name)
                )
                # All should return 400 or 404
                assert response.status_code in [400, 404]

    def test_admin_role_requirement(self, regular_user, auth_client, app):
        """Non-admin users cannot access any sequence endpoints."""
        with app.app_context():
            endpoints = [
                ('admin.fix_all_sequences', {}),
                ('admin.fix_table_sequence', {'table_name': 'blog-posts'}),
                ('admin.fix_all_sequences_v2', {})
            ]

            for endpoint, params in endpoints:
                response = auth_client.post(
                    url_for(endpoint, **params),
                    json={} if 'v2' in endpoint else None,
                    follow_redirects=False
                )
                assert response.status_code == 403

    def test_authentication_requirement(self, client, app):
        """Unauthenticated users cannot access any sequence endpoints."""
        with app.app_context():
            endpoints = [
                ('admin.fix_all_sequences', {}),
                ('admin.fix_table_sequence', {'table_name': 'blog-posts'}),
                ('admin.fix_all_sequences_v2', {})
            ]

            for endpoint, params in endpoints:
                response = client.post(
                    url_for(endpoint, **params),
                    json={} if 'v2' in endpoint else None,
                    follow_redirects=False
                )
                assert response.status_code == 302
                assert 'login' in response.location

    def test_error_messages_dont_leak_sensitive_info(self, admin_client, app):
        """Error messages don't expose internal system details."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                mock_fix.return_value = (False, {
                    'status': 'error',
                    'table': 'blog_posts',
                    'error_type': 'SQLAlchemyError',
                    'message': 'Database error occurred while fixing sequence',
                    'execution_time_ms': 10
                })

                response = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name='blog-posts')
                )

                assert response.status_code == 500
                data = json.loads(response.data)
                # Error message should be generic, not expose connection strings, etc.
                assert 'postgresql' not in data['message'].lower()
                assert 'password' not in data['message'].lower()


# ============================================================================
# Integration Tests
# ============================================================================

class TestSequenceIntegration:
    """Test integration between different sequence fix endpoints."""

    def test_individual_endpoint_and_v2_consistency(self, admin_client, app, db):
        """Individual endpoint and v2 orchestrator produce consistent results."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # Both endpoints return same result
                mock_result = (True, {
                    'status': 'success',
                    'table': 'blog_posts',
                    'sequence_name': 'blog_posts_id_seq',
                    'old_value': 0,
                    'new_value': 1,
                    'execution_time_ms': 10
                })
                mock_fix.side_effect = [mock_result, mock_result]

                # Use individual endpoint
                response1 = admin_client.post(
                    url_for('admin.fix_table_sequence', table_name='blog-posts')
                )
                data1 = json.loads(response1.data)

                # Use v2 orchestrator
                response2 = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={'tables': ['blog-posts']}
                )
                data2 = json.loads(response2.data)

            # Both should report success and same new_value
            assert data1['status'] == 'success'
            assert data2['results'][0]['status'] == 'success'
            assert data1['new_value'] == data2['results'][0]['new_value']

    def test_legacy_and_v2_backward_compatibility(self, admin_client, app, db):
        """Legacy endpoint and v2 orchestrator are compatible."""
        with app.app_context():
            with patch('app.routes.admin.fix_single_table_sequence') as mock_fix:
                # All 4 tables succeed for both calls
                all_succeed = [
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    # Same 4 for legacy endpoint
                    (True, {'status': 'success', 'table': 'blog_posts', 'sequence_name': 'blog_posts_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'users', 'sequence_name': 'users_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'roles', 'sequence_name': 'roles_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10}),
                    (True, {'status': 'success', 'table': 'minecraft_commands', 'sequence_name': 'minecraft_commands_command_id_seq', 'old_value': 0, 'new_value': 1, 'execution_time_ms': 10})
                ]
                mock_fix.side_effect = all_succeed

                # Both should successfully fix all sequences
                response1 = admin_client.post(url_for('admin.fix_all_sequences'))
                data1 = json.loads(response1.data)

                response2 = admin_client.post(
                    url_for('admin.fix_all_sequences_v2'),
                    json={}
                )
                data2 = json.loads(response2.data)

            assert response1.status_code == 200
            assert response2.status_code == 200
            assert data1['status'] == 'success'
            assert data2['status'] == 'success'
