# tests/test_simple.py
# A minimal test file to verify setup works

import pytest
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that we can import the app modules."""
    try:
        from app import create_app, db
        from app.models import BlogPost, User
        from app.routes_blogpost import blogpost_bp
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_create_app_with_test_config():
    """Test creating app with test configuration."""
    # Override database URL before importing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    from app import create_app, db
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        assert app is not None
        assert app.config['TESTING'] is True

def test_blogpost_blueprint_registered():
    """Test that blogpost blueprint is registered."""
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    from app import create_app
    
    app = create_app()
    
    # Check if blueprint is registered
    assert 'blogpost_bp' in app.blueprints

def test_simple_route():
    """Test a simple GET request."""
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    from app import create_app, db
    from app.models import BlogPost
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create a test post
        post = BlogPost(title='Test', content='Content')
        db.session.add(post)
        db.session.commit()
        post_id = post.id
        
        # Test with client
        client = app.test_client()
        response = client.get(f'/post/{post_id}')
        
        assert response.status_code == 200
        assert b'Test' in response.data

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])