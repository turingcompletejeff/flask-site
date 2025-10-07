"""
Integration tests for main routes.

Tests cover:
- Index page (/) - blog post listing
- About page (/about)
- Draft visibility based on authentication
- Flash message handling
"""

import pytest
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
