# ============================================
# tests/test_routes_blogpost.py
# ============================================

import pytest
from io import BytesIO
from PIL import Image


class TestBlogPostRoutes:
    """Test blog post routes."""
    
    def test_view_post(self, client, sample_post):
        """Test viewing a blog post."""
        response = client.get(f'/post/{sample_post}')
        assert response.status_code == 200
        assert b'Test Post' in response.data
    
    def test_view_nonexistent_post(self, client):
        """Test 404 for non-existent post."""
        response = client.get('/post/9999')
        assert response.status_code == 404
    
    def test_new_post_requires_auth(self, client):
        """Test authentication required for new post."""
        response = client.get('/post/new')
        assert response.status_code == 302
        assert 'login' in response.location.lower()
    
    def test_create_post(self, auth_client, app):
        """Test creating a new post."""
        from app.models import BlogPost
        
        response = auth_client.post('/post/new', data={
            'title': 'New Post',
            'content': 'New content'
        }, follow_redirects=True)
        
        with app.app_context():
            post = BlogPost.query.filter_by(title='New Post').first()
            assert post is not None
            assert post.content == 'New content'
    
    def test_create_post_with_image(self, auth_client, app):
        """Test creating post with image upload."""
        from app.models import BlogPost
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        
        response = auth_client.post('/post/new', data={
            'title': 'Post with Image',
            'content': 'Content',
            'portrait': (img_io, 'test.jpg')
        }, content_type='multipart/form-data', follow_redirects=True)
        
        with app.app_context():
            post = BlogPost.query.filter_by(title='Post with Image').first()
            assert post is not None
            assert post.portrait == 'test.jpg'
            assert post.thumbnail == 'thumb_test.jpg'
    
    def test_edit_post(self, auth_client, sample_post, app):
        """Test editing a post."""
        from app.models import BlogPost
        
        # GET edit page
        response = auth_client.get(f'/post/{sample_post}/edit')
        assert response.status_code == 200
        assert b'Test Post' in response.data
        
        # POST update
        response = auth_client.post(f'/post/{sample_post}/edit', data={
            'title': 'Updated Title',
            'content': 'Updated content'
        }, follow_redirects=True)
        
        with app.app_context():
            post = BlogPost.query.get(sample_post)
            assert post.title == 'Updated Title'
            assert post.content == 'Updated content'
    
    def test_delete_post(self, auth_client, sample_post, app):
        """Test deleting a post."""
        from app.models import BlogPost
        
        response = auth_client.post('/post/delete', data={
            'id': sample_post
        }, follow_redirects=True)
        
        with app.app_context():
            post = BlogPost.query.get(sample_post)
            assert post is None

