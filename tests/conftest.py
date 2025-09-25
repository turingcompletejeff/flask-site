# tests/conftest.py
"""
Shared test configuration and fixtures.
This file is automatically loaded by pytest.
"""

import pytest
import tempfile
import json
from sqlalchemy import Text, TypeDecorator

# Database compatibility layer for PostgreSQL → SQLite
class JSONType(TypeDecorator):
    """Store JSON as Text in SQLite, as JSON in PostgreSQL."""
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name == 'sqlite':
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None and dialect.name == 'sqlite':
            return json.loads(value)
        return value


class ArrayType(TypeDecorator):
    """Store ARRAY as JSON-encoded Text in SQLite."""
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name == 'sqlite':
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None and dialect.name == 'sqlite':
            return json.loads(value)
        return value


@pytest.fixture(scope='function')
def app():
    """Create application with test configuration."""
    from app import create_app, db
    
    # Create app with test config
    test_app = create_app()
    
    # Override configuration for testing
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'BLOG_POST_UPLOAD_FOLDER': tempfile.mkdtemp(),
        'LOGIN_DISABLED': False,
    })
    
    with test_app.app_context():
        # Monkey-patch PostgreSQL types for SQLite compatibility
        _patch_postgresql_types()
        
        # Import models after patching
        from app.models import User, BlogPost, MinecraftCommand
        
        # Create tables
        db.create_all()
        
        yield test_app
        
        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def auth_user(app):
    """Create a test user for authentication."""
    from app import db
    from app.models import User
    
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture(scope='function')
def auth_client(client, auth_user):
    """Create an authenticated test client."""
    # Login the user
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    }, follow_redirects=True)
    
    return client


@pytest.fixture(scope='function')
def sample_post(app):
    """Create a sample blog post."""
    from app import db
    from app.models import BlogPost
    
    with app.app_context():
        post = BlogPost(
            title='Test Post',
            content='Test content',
            themap={'key': 'value'}  # Test JSON field
        )
        db.session.add(post)
        db.session.commit()
        return post.id


def _patch_postgresql_types():
    """Patch PostgreSQL-specific types for SQLite compatibility."""
    import sqlalchemy.dialects.postgresql as pg
    import sqlalchemy
    
    # Save originals
    original_array = pg.ARRAY
    original_json = pg.JSON
    
    # Create compatible versions
    pg.ARRAY = lambda *args, **kwargs: ArrayType()
    pg.JSON = lambda *args, **kwargs: JSONType()
    
    # Also patch main sqlalchemy if they're there
    if hasattr(sqlalchemy, 'ARRAY'):
        sqlalchemy.ARRAY = lambda *args, **kwargs: ArrayType()
    if hasattr(sqlalchemy, 'JSON'):
        sqlalchemy.JSON = lambda *args, **kwargs: JSONType()
