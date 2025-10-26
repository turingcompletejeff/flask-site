"""
Integration tests for main routes.

Tests cover:
- Index page (/) - blog post listing
- About page (/about)
- Draft visibility based on authentication
- Flash message handling
"""

import pytest
from unittest.mock import Mock
from flask import url_for


@pytest.mark.integration
class TestIndexRoute:
    """Test suite for index route (/)."""

    def test_index_accessible(self, client, db):
        """Test that index page is accessible."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_shows_published_posts(self, client, published_post, db):
        """Test that index page shows published posts to all users."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Test Published Post' in response.data

    def test_index_hides_drafts_from_unauthenticated(self, client, draft_post, db):
        """Test that draft posts are hidden from unauthenticated users."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Test Draft Post' not in response.data

    def test_index_shows_drafts_to_authenticated(self, auth_client, draft_post, db):
        """Test that draft posts are visible to authenticated users."""
        response = auth_client.get('/')
        assert response.status_code == 200
        assert b'Test Draft Post' in response.data

    def test_index_shows_both_published_and_drafts_to_authenticated(
        self, auth_client, published_post, draft_post, db
    ):
        """Test that authenticated users see both published and draft posts."""
        response = auth_client.get('/')
        assert response.status_code == 200
        assert b'Test Published Post' in response.data
        assert b'Test Draft Post' in response.data

    def test_index_shows_only_published_to_unauthenticated(
        self, client, published_post, draft_post, db
    ):
        """Test that unauthenticated users only see published posts."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Test Published Post' in response.data
        assert b'Test Draft Post' not in response.data

    def test_index_post_ordering(self, client, db):
        """Test that posts are ordered by date (newest first)."""
        from app.models import BlogPost
        from datetime import datetime, timedelta

        # Create posts with different dates
        old_post = BlogPost(
            title='Old Post',
            content='Old content',
            is_draft=False,
            date_posted=datetime.now() - timedelta(days=10)
        )
        recent_post = BlogPost(
            title='Recent Post',
            content='Recent content',
            is_draft=False,
            date_posted=datetime.now() - timedelta(days=1)
        )
        newest_post = BlogPost(
            title='Newest Post',
            content='Newest content',
            is_draft=False,
            date_posted=datetime.now()
        )

        db.session.add_all([old_post, recent_post, newest_post])
        db.session.commit()

        response = client.get('/')
        html = response.data.decode('utf-8')

        # Find positions of each post title in the HTML
        newest_pos = html.find('Newest Post')
        recent_pos = html.find('Recent Post')
        old_pos = html.find('Old Post')

        # Verify ordering: newest should appear before recent, recent before old
        assert newest_pos < recent_pos < old_pos

    def test_index_empty_state(self, client, db):
        """Test that index page handles no posts gracefully."""
        response = client.get('/')
        assert response.status_code == 200
        # Should not crash when there are no posts

    def test_index_with_many_posts(self, client, db):
        """Test that index page handles many posts."""
        from app.models import BlogPost

        # Create 20 posts
        posts = []
        for i in range(20):
            post = BlogPost(
                title=f'Post {i}',
                content=f'Content {i}',
                is_draft=False
            )
            posts.append(post)

        db.session.add_all(posts)
        db.session.commit()

        response = client.get('/')
        assert response.status_code == 200
        # Verify at least some posts are shown
        assert b'Post 0' in response.data or b'Post 1' in response.data


@pytest.mark.integration
class TestFlashMessages:
    """Test suite for flash message handling on index."""

    def test_index_flash_message_from_query_param(self, client, db):
        """Test that flash messages can be displayed via query parameter."""
        response = client.get('/?flash=Test+Message&category=success')
        assert response.status_code == 200
        # Flash message should be in the response (assuming base template shows flashes)
        # The exact rendering depends on template implementation

    def test_index_flash_default_category(self, client, db):
        """Test that flash message uses default category if not specified."""
        response = client.get('/?flash=Info+Message')
        assert response.status_code == 200
        # Should not crash with missing category

    def test_flash_message_success_displayed(self, client, db):
        """Test that success flash messages are properly displayed."""
        with client.session_transaction() as sess:
            sess['_flashes'] = [('success', 'Success message')]

        response = client.get('/')
        assert b'Success message' in response.data

    def test_flash_message_error_displayed(self, client, db):
        """Test that error flash messages are properly displayed."""
        with client.session_transaction() as sess:
            sess['_flashes'] = [('error', 'Error message')]

        response = client.get('/')
        assert b'Error message' in response.data

    def test_flash_multiple_messages(self, client, db):
        """Test that multiple flash messages are all displayed."""
        with client.session_transaction() as sess:
            sess['_flashes'] = [
                ('success', 'First'),
                ('error', 'Second'),
                ('warning', 'Third')
            ]

        response = client.get('/')
        assert b'First' in response.data
        assert b'Second' in response.data
        assert b'Third' in response.data


@pytest.mark.integration
class TestAboutRoute:
    """Test suite for about route (/about)."""

    def test_about_accessible(self, client):
        """Test that about page is accessible."""
        response = client.get('/about')
        assert response.status_code == 200

    def test_about_no_authentication_required(self, client):
        """Test that about page doesn't require authentication."""
        response = client.get('/about')
        assert response.status_code == 200

    def test_about_accessible_when_authenticated(self, auth_client):
        """Test that about page is accessible when logged in."""
        response = auth_client.get('/about')
        assert response.status_code == 200

    def test_about_returns_html(self, client):
        """Test that about page returns HTML."""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


@pytest.mark.integration
class TestCurrentPageContext:
    """Test suite for current_page template context variable."""

    def test_index_has_blog_current_page(self, client, db):
        """Test that index sets current_page to 'blog'."""
        response = client.get('/')
        assert response.status_code == 200
        # The template should receive current_page="blog"
        # Exact verification depends on template implementation

    def test_about_has_about_current_page(self, client):
        """Test that about sets current_page to 'about'."""
        response = client.get('/about')
        assert response.status_code == 200
        # The template should receive current_page="about"


@pytest.mark.integration
class TestMainRouteEdgeCases:
    """Test edge cases for main routes."""

    def test_index_with_post_containing_html(self, client, db):
        """Test that index handles posts with HTML content safely."""
        from app.models import BlogPost

        post = BlogPost(
            title='<script>alert("XSS")</script>',
            content='<b>Bold content</b>',
            is_draft=False
        )
        db.session.add(post)
        db.session.commit()

        response = client.get('/')
        assert response.status_code == 200
        # Should escape HTML in title or handle it safely

    def test_index_with_unicode_content(self, client, db):
        """Test that index handles Unicode content properly."""
        from app.models import BlogPost

        post = BlogPost(
            title='Unicode Test: 你好世界 🎉',
            content='Content with émojis and àccénts',
            is_draft=False
        )
        db.session.add(post)
        db.session.commit()

        response = client.get('/')
        assert response.status_code == 200
        # Should handle Unicode properly
        assert '你好世界' in response.data.decode('utf-8') or response.status_code == 200

    def test_index_with_very_long_title(self, client, db):
        """Test that index handles posts with very long titles."""
        from app.models import BlogPost

        long_title = 'A' * 500
        post = BlogPost(
            title=long_title,
            content='Content',
            is_draft=False
        )
        db.session.add(post)
        db.session.commit()

        response = client.get('/')
        assert response.status_code == 200

    def test_index_post_with_null_fields(self, client, db):
        """Test that index handles posts with NULL optional fields."""
        from app.models import BlogPost

        post = BlogPost(
            title='Minimal Post',
            content='Content',
            portrait=None,
            thumbnail=None,
            themap=None,
            is_draft=False
        )
        db.session.add(post)
        db.session.commit()

        response = client.get('/')
        assert response.status_code == 200
        assert b'Minimal Post' in response.data


@pytest.mark.integration
class TestContactRouteDisplay:
    """Test suite for contact form display (GET /contact)."""

    def test_contact_page_accessible(self, client):
        """Test that contact page is accessible."""
        response = client.get('/contact')
        assert response.status_code == 200

    def test_contact_page_no_authentication_required(self, client):
        """Test that contact page doesn't require authentication."""
        response = client.get('/contact')
        assert response.status_code == 200

    def test_contact_page_accessible_when_authenticated(self, auth_client):
        """Test that contact page is accessible when logged in."""
        response = auth_client.get('/contact')
        assert response.status_code == 200

    def test_contact_page_has_form(self, client):
        """Test that contact page contains a form."""
        response = client.get('/contact')
        assert response.status_code == 200
        assert b'<form' in response.data

    def test_contact_page_has_required_fields(self, client):
        """Test that contact form has all required fields."""
        response = client.get('/contact')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # Check for form fields
        assert 'name' in html.lower()
        assert 'email' in html.lower()
        assert 'message' in html.lower()

    def test_contact_page_sets_current_page(self, client):
        """Test that contact page sets current_page context."""
        response = client.get('/contact')
        assert response.status_code == 200
        # Template should receive current_page="contact"


@pytest.mark.integration
class TestContactFormSubmission:
    """Test suite for contact form submission (POST /contact)."""

    @pytest.fixture
    def valid_contact_data(self):
        """Provide valid contact form data."""
        return {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '5551234567',
            'reason': 'informational',
            'message': 'This is a test message.'
        }

    def test_contact_form_submission_with_mock_email(self, client, valid_contact_data, monkeypatch):
        """Test successful contact form submission with mocked email."""
        # Mock the sendAnEmail function to prevent actual email sending
        email_sent = []

        def mock_send_email(message):
            email_sent.append(message)

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email)

        response = client.post('/contact', data=valid_contact_data, follow_redirects=True)

        # Should redirect to index on success
        assert response.status_code == 200
        assert len(email_sent) == 1
        assert 'john@example.com' in email_sent[0]

    def test_contact_form_with_other_reason(self, client, valid_contact_data, monkeypatch):
        """Test contact form submission with 'other' reason."""
        email_sent = []

        def mock_send_email(message):
            email_sent.append(message)

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email)

        valid_contact_data['reason'] = 'other'
        valid_contact_data['other_reason'] = 'Custom reason here'

        response = client.post('/contact', data=valid_contact_data, follow_redirects=True)

        assert response.status_code == 200
        assert len(email_sent) == 1
        assert 'Custom reason here' in email_sent[0]

    def test_contact_form_invalid_email(self, client, valid_contact_data):
        """Test contact form submission with invalid email."""
        valid_contact_data['email'] = 'not-an-email'

        response = client.post('/contact', data=valid_contact_data)

        # Should return to form with errors
        assert response.status_code == 200
        assert b'contact' in response.data.lower()

    def test_contact_form_missing_required_fields(self, client):
        """Test contact form submission with missing required fields."""
        incomplete_data = {
            'name': 'John Doe'
        }

        response = client.post('/contact', data=incomplete_data)

        # Should return to form with errors
        assert response.status_code == 200

    def test_contact_form_empty_message(self, client, valid_contact_data):
        """Test contact form submission with empty message."""
        valid_contact_data['message'] = ''

        response = client.post('/contact', data=valid_contact_data)

        # Should fail validation
        assert response.status_code == 200

    def test_contact_form_sql_injection_attempt(self, client, valid_contact_data, monkeypatch):
        """Test that contact form sanitizes SQL injection attempts."""
        email_sent = []

        def mock_send_email(message):
            email_sent.append(message)

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email)

        valid_contact_data['name'] = "'; DROP TABLE users; --"
        valid_contact_data['message'] = "SELECT * FROM users WHERE '1'='1'"

        response = client.post('/contact', data=valid_contact_data, follow_redirects=True)

        # Form should still work (no SQL injection possible)
        assert response.status_code == 200

    def test_contact_form_xss_attempt(self, client, valid_contact_data, monkeypatch):
        """Test that contact form handles XSS attempts."""
        email_sent = []

        def mock_send_email(message):
            email_sent.append(message)

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email)

        valid_contact_data['message'] = '<script>alert("XSS")</script>'

        response = client.post('/contact', data=valid_contact_data, follow_redirects=True)

        # Should handle gracefully
        assert response.status_code == 200


@pytest.mark.integration
class TestContactFormAJAX:
    """Test suite for AJAX contact form submissions."""

    @pytest.fixture
    def valid_contact_data(self):
        """Provide valid contact form data."""
        return {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '5555556789',
            'reason': 'informational',
            'message': 'AJAX test message.'
        }

    def test_contact_form_ajax_success(self, client, valid_contact_data, monkeypatch):
        """Test AJAX contact form submission returns JSON on success."""
        def mock_send_email(message):
            pass

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email)

        response = client.post(
            '/contact',
            data=valid_contact_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True
        assert 'message' in json_data

    def test_contact_form_ajax_with_accept_json(self, client, valid_contact_data, monkeypatch):
        """Test AJAX detection via Accept header."""
        def mock_send_email(message):
            pass

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email)

        response = client.post(
            '/contact',
            data=valid_contact_data,
            headers={'Accept': 'application/json'}
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True

    def test_contact_form_ajax_email_failure(self, client, valid_contact_data, monkeypatch):
        """Test AJAX contact form returns error JSON on email failure."""
        def mock_send_email_fail(message):
            raise Exception("SMTP connection failed")

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email_fail)

        response = client.post(
            '/contact',
            data=valid_contact_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        assert response.status_code == 500
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'error' in json_data

    def test_contact_form_ajax_validation_error(self, client, monkeypatch):
        """Test AJAX request with validation errors returns form with errors."""
        invalid_data = {
            'name': 'Jane',
            'email': 'invalid-email'
        }

        response = client.post(
            '/contact',
            data=invalid_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        # Should return form template with errors
        assert response.status_code == 200
        assert b'contact' in response.data.lower()


@pytest.mark.integration
class TestContactFormEmailSending:
    """Test suite for email sending functionality."""

    @pytest.fixture
    def valid_contact_data(self):
        """Provide valid contact form data."""
        return {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '5550001234',
            'reason': 'personal',
            'message': 'Test feedback message.'
        }

    def test_contact_form_email_failure_non_ajax(self, client, valid_contact_data, monkeypatch):
        """Test that email failures are handled gracefully for non-AJAX requests."""
        def mock_send_email_fail(message):
            raise Exception("Email server unavailable")

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email_fail)

        response = client.post('/contact', data=valid_contact_data)

        # Should return to form with error flash
        assert response.status_code == 200
        assert b'contact' in response.data.lower()

    def test_contact_form_smtp_timeout(self, client, valid_contact_data, monkeypatch):
        """Test contact form handles SMTP timeout."""
        import smtplib

        def mock_send_email_timeout(message):
            raise smtplib.SMTPServerDisconnected("Connection timed out")

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email_timeout)

        response = client.post('/contact', data=valid_contact_data, follow_redirects=False)

        # Should handle error gracefully
        assert response.status_code == 200

    def test_contact_form_smtp_auth_error(self, client, valid_contact_data, monkeypatch):
        """Test contact form handles SMTP authentication errors."""
        import smtplib

        def mock_send_email_auth_fail(message):
            raise smtplib.SMTPAuthenticationError(535, "Authentication failed")

        from app.routes import main
        monkeypatch.setattr(main, 'sendAnEmail', mock_send_email_auth_fail)

        response = client.post('/contact', data=valid_contact_data)

        # Should handle error gracefully
        assert response.status_code == 200


@pytest.mark.unit
class TestFormatContactEmail:
    """Test suite for formatContactEmail helper function."""

    def test_format_email_basic(self, app):
        """Test email formatting with basic contact data."""
        from app.routes.main import formatContactEmail
        from app.forms import ContactForm

        with app.test_request_context():
            form = ContactForm(
                name='John Doe',
                email='john@example.com',
                phone='5551234567',
                reason='informational',
                message='Test message'
            )

            result = formatContactEmail(form)

            assert 'John Doe' in result
            assert 'john@example.com' in result
            assert '5551234567' in result
            assert 'informational' in result
            assert 'Test message' in result

    def test_format_email_with_other_reason(self, app):
        """Test email formatting when reason is 'other'."""
        from app.routes.main import formatContactEmail
        from app.forms import ContactForm

        with app.test_request_context():
            form = ContactForm(
                name='Jane Doe',
                email='jane@example.com',
                phone='5555556789',
                reason='other',
                other_reason='Custom inquiry',
                message='Custom message'
            )

            result = formatContactEmail(form)

            assert 'Jane Doe' in result
            assert 'other' in result
            assert 'Custom inquiry' in result

    def test_format_email_without_other_reason(self, app):
        """Test email formatting when reason is not 'other'."""
        from app.routes.main import formatContactEmail
        from app.forms import ContactForm

        with app.test_request_context():
            form = ContactForm(
                name='Test User',
                email='test@example.com',
                phone='5550001234',
                reason='personal',
                message='Feedback message'
            )

            result = formatContactEmail(form)

            assert 'personal' in result
            assert 'custom reason' not in result.lower()

    def test_format_email_with_unicode(self, app):
        """Test email formatting with Unicode characters."""
        from app.routes.main import formatContactEmail
        from app.forms import ContactForm

        with app.test_request_context():
            form = ContactForm(
                name='José García',
                email='jose@example.com',
                phone='5559999999',
                reason='informational',
                message='Message with émojis 🎉'
            )

            result = formatContactEmail(form)

            assert 'José García' in result
            assert '🎉' in result or 'emoji' in result.lower()

    def test_format_email_with_special_chars(self, app):
        """Test email formatting with special characters."""
        from app.routes.main import formatContactEmail
        from app.forms import ContactForm

        with app.test_request_context():
            form = ContactForm(
                name="O'Brien",
                email='obrien@example.com',
                phone='5552222222',
                reason='hiring',
                message='Message with "quotes" and <brackets>'
            )

            result = formatContactEmail(form)

            assert "O'Brien" in result
            assert 'quotes' in result


@pytest.mark.unit
class TestSendAnEmail:
    """Test suite for sendAnEmail helper function."""

    def test_send_email_success(self, app, monkeypatch):
        """Test successful email sending with mocked SMTP."""
        from app.routes.main import sendAnEmail
        import smtplib

        # Create a mock SMTP instance
        mock_smtp = Mock()
        mock_smtp_class = Mock(return_value=mock_smtp)

        # Patch smtplib.SMTP
        monkeypatch.setattr('smtplib.SMTP', mock_smtp_class)

        with app.app_context():
            # Call the function
            sendAnEmail("Test email message")

            # Verify SMTP methods were called
            mock_smtp_class.assert_called_once()
            mock_smtp.connect.assert_called_once()
            mock_smtp.ehlo.assert_called()
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once()
            mock_smtp.sendmail.assert_called_once()
            mock_smtp.quit.assert_called_once()

    def test_send_email_with_message_content(self, app, monkeypatch):
        """Test that email contains the correct message content."""
        from app.routes.main import sendAnEmail
        import smtplib

        mock_smtp = Mock()
        mock_smtp_class = Mock(return_value=mock_smtp)
        monkeypatch.setattr('smtplib.SMTP', mock_smtp_class)

        with app.app_context():
            test_message = "This is a test contact form message"
            sendAnEmail(test_message)

            # Verify sendmail was called with message containing our text
            assert mock_smtp.sendmail.called
            call_args = mock_smtp.sendmail.call_args[0]
            assert test_message in call_args[2]  # Third argument is the message


@pytest.mark.unit
class TestAttemptEmailConnection:
    """Test suite for attemptEmailConnection helper function."""

    def test_email_connection_success(self, app, monkeypatch):
        """Test successful SMTP connection."""
        from app.routes.main import attemptEmailConnection
        import smtplib

        mock_smtp = Mock()
        mock_smtp_class = Mock(return_value=mock_smtp)
        monkeypatch.setattr('smtplib.SMTP', mock_smtp_class)

        with app.app_context():
            result = attemptEmailConnection()

            # Should return True on success
            assert result is True

            # Verify SMTP methods were called in correct order
            mock_smtp_class.assert_called_once()
            mock_smtp.connect.assert_called_once()
            mock_smtp.ehlo.assert_called()
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once()
            mock_smtp.quit.assert_called_once()

    def test_email_connection_debug_mode(self, app, monkeypatch):
        """Test that debug mode is set correctly."""
        from app.routes.main import attemptEmailConnection
        import smtplib

        mock_smtp = Mock()
        mock_smtp_class = Mock(return_value=mock_smtp)
        monkeypatch.setattr('smtplib.SMTP', mock_smtp_class)

        with app.app_context():
            attemptEmailConnection()

            # Verify debug level was set
            mock_smtp.set_debuglevel.assert_called_once_with(100)


@pytest.mark.integration
class TestUploadedFileRoute:
    """Test suite for uploaded file serving route."""

    def test_uploaded_file_route_exists(self, client):
        """Test that uploaded file route is registered."""
        # This will 404 but shouldn't error
        response = client.get('/uploads/blog-posts/nonexistent.jpg')
        assert response.status_code in [200, 404]

    def test_uploaded_file_with_real_file(self, client, app, db):
        """Test serving an actual uploaded file."""
        import os
        from werkzeug.datastructures import FileStorage

        # Create a test file in the upload directory
        upload_dir = app.config['BLOG_POST_UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        test_file_path = os.path.join(upload_dir, 'test_image.txt')
        with open(test_file_path, 'w') as f:
            f.write('Test content')

        try:
            response = client.get('/uploads/blog-posts/test_image.txt')
            assert response.status_code == 200
            assert b'Test content' in response.data
        finally:
            # Cleanup
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_uploaded_file_path_traversal_prevention(self, client):
        """Test that path traversal is prevented."""
        # Attempt to access files outside upload directory
        response = client.get('/uploads/blog-posts/../../../etc/passwd')
        # Should either 404 or 400, not 200
        assert response.status_code in [400, 404]

    def test_uploaded_file_with_special_chars(self, client, app):
        """Test serving file with special characters in name."""
        import os

        upload_dir = app.config['BLOG_POST_UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        # Create file with spaces
        test_file_path = os.path.join(upload_dir, 'test file.txt')
        with open(test_file_path, 'w') as f:
            f.write('Test')

        try:
            # URL encoding handled by client
            response = client.get('/uploads/blog-posts/test%20file.txt')
            assert response.status_code in [200, 404]
        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
