# ============================================
# tests/test_auth.py
# ============================================

import pytest


class TestAuthentication:
    """Test authentication routes."""
    
    def test_register_get(self, client, app):
        """Test registration page loads."""
        # Only test if registration is enabled
        if app.config.get('REGISTRATION_ENABLED', True):
            response = client.get('/register')
            assert response.status_code == 200
            assert b'register' in response.data.lower()
    
    def test_register_post(self, client, app):
        """Test user registration."""
        from app.models import User
        
        if app.config.get('REGISTRATION_ENABLED', True):
            response = client.post('/register', data={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123',
                'confirm_password': 'password123'
            }, follow_redirects=True)
            
            with app.app_context():
                user = User.query.filter_by(username='newuser').first()
                assert user is not None
                assert user.email == 'new@example.com'
    
    def test_login_logout(self, client, auth_user):
        """Test login and logout."""
        # Login
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Access protected route
        response = client.get('/post/new')
        assert response.status_code == 200  # Should work when logged in
        
        # Logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Try protected route again
        response = client.get('/post/new')
        assert response.status_code == 302  # Should redirect when logged out

