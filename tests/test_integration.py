# ============================================
# tests/test_integration.py  
# ============================================

import pytest


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_blog_workflow(self, client, app):
        """Test complete blog post lifecycle."""
        from app.models import User, BlogPost
        
        with app.app_context():
            # Register user
            if app.config.get('REGISTRATION_ENABLED', True):
                client.post('/register', data={
                    'username': 'blogger',
                    'email': 'blogger@test.com',
                    'password': 'password123',
                    'confirm_password': 'password123'
                })
            else:
                # Create user directly if registration disabled
                user = User(username='blogger', email='blogger@test.com')
                user.set_password('password123')
                from app import db
                db.session.add(user)
                db.session.commit()
            
            # Login
            client.post('/login', data={
                'username': 'blogger',
                'password': 'password123'
            })
            
            # Create post
            client.post('/post/new', data={
                'title': 'My First Post',
                'content': 'This is my content'
            })
            
            # Verify post exists
            post = BlogPost.query.filter_by(title='My First Post').first()
            assert post is not None
            post_id = post.id
            
            # View post (logged out)
            client.get('/logout')
            response = client.get(f'/post/{post_id}')
            assert response.status_code == 200
            assert b'My First Post' in response.data
            
            # Edit post (requires login)
            response = client.get(f'/post/{post_id}/edit')
            assert response.status_code == 302  # Redirect to login
            
            # Login again and edit
            client.post('/login', data={
                'username': 'blogger', 
                'password': 'password123'
            })
            
            client.post(f'/post/{post_id}/edit', data={
                'title': 'Updated Post',
                'content': 'Updated content'
            })
            
            # Verify changes
            post = BlogPost.query.get(post_id)
            assert post.title == 'Updated Post'
            
            # Delete post
            client.post('/post/delete', data={'id': post_id})
            
            # Verify deletion
            post = BlogPost.query.get(post_id)
            assert post is None


# ============================================
# Run tests
# ============================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])