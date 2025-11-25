"""
Pytest configuration and fixtures for Flask portfolio application tests.

Provides fixtures for:
- Flask app instances (with in-memory SQLite)
- Database setup and teardown
- Test clients (unauthenticated and authenticated)
- User fixtures (regular, blogger, admin)
- Role fixtures
- BlogPost fixtures
- CSRF token handling
- Mock file uploads
- Mock RCON connection
"""

import os
import io
import sys
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from flask import url_for, Flask
from flask_sqlalchemy import SQLAlchemy

# Set TESTING environment variable BEFORE any app imports
# This ensures Config class uses SQLite instead of PostgreSQL
os.environ['TESTING'] = 'true'

# Import create_app and db for fixtures to use
from app import create_app, db as _db
from app.models import User, Role, BlogPost, MinecraftCommand, MinecraftLocation


# Mock the database connection in app/__init__.py BEFORE importing
# This prevents create_app from trying to connect to PostgreSQL
@pytest.fixture(scope='function')
def app():
    """
    Create and configure a test Flask application instance.

    Uses in-memory SQLite database for fast, isolated tests.
    Disables CSRF protection for easier testing.
    """
    # Import necessary modules
    import os
    from pathlib import Path

    # Determine the template folder path (app/templates)
    app_dir = Path(__file__).parent.parent / 'app'
    template_folder = str(app_dir / 'templates')
    static_folder = str(app_dir / 'static')

    # Create Flask app manually with correct template folder
    test_app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {},  # Override PostgreSQL-specific options
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for most tests
        'SECRET_KEY': 'test-secret-key',
        'BLOG_POST_UPLOAD_FOLDER': '/tmp/test-blog-posts',
        'PROFILE_UPLOAD_FOLDER': '/tmp/test-profiles',
        'MC_LOCATION_UPLOAD_FOLDER': '/tmp/test-minecraft-locations',
        'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,
        'REGISTRATION_ENABLED': True,
        'SERVER_NAME': 'localhost.localdomain'  # Required for url_for outside request context
    })

    # Initialize extensions
    from flask_wtf import CSRFProtect
    from flask_migrate import Migrate
    from flask_login import LoginManager

    csrf = CSRFProtect()
    csrf.init_app(test_app)

    _db.init_app(test_app)
    migrate = Migrate(test_app, _db)

    login_manager = LoginManager()
    login_manager.init_app(test_app)
    login_manager.login_view = 'auth.login'  # Critical: enables proper 302 redirects

    # Register filters
    from app.utils.filters import register_filters
    register_filters(test_app)

    # Create upload directories
    os.makedirs(test_app.config['BLOG_POST_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(test_app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(test_app.config['MC_LOCATION_UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.routes import (
        main_bp,
        auth_bp,
        blogpost_bp,
        mc_bp,
        mc_commands_bp,
        admin_bp,
        health_bp,
        profile_bp
    )

    test_app.register_blueprint(main_bp)
    test_app.register_blueprint(auth_bp)
    test_app.register_blueprint(blogpost_bp)
    test_app.register_blueprint(mc_bp)
    test_app.register_blueprint(mc_commands_bp)
    test_app.register_blueprint(health_bp)
    test_app.register_blueprint(profile_bp)
    test_app.register_blueprint(admin_bp)

    # Exempt health endpoint from CSRF
    csrf.exempt(health_bp)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Establish application context
    with test_app.app_context():
        yield test_app

        # Close database connections before cleanup
        _db.session.remove()
        _db.engine.dispose()

    # Cleanup upload directories after tests
    import shutil
    for folder in [test_app.config['BLOG_POST_UPLOAD_FOLDER'],
                   test_app.config['PROFILE_UPLOAD_FOLDER']]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)


@pytest.fixture(scope='function')
def db(app):
    """
    Create a fresh database for each test.

    Creates all tables before test, drops all tables after test.
    Ensures complete isolation between tests.

    Note: Now includes MinecraftCommand with StringArray type (cross-database compatible).
    """
    from app.models import User, Role, BlogPost, MinecraftCommand, MinecraftLocation, role_assignments

    with app.app_context():
        # Create all tables (MinecraftCommand now uses StringArray for SQLite compatibility)
        User.__table__.create(_db.engine, checkfirst=True)
        Role.__table__.create(_db.engine, checkfirst=True)
        BlogPost.__table__.create(_db.engine, checkfirst=True)
        MinecraftCommand.__table__.create(_db.engine, checkfirst=True)
        MinecraftLocation.__table__.create(_db.engine, checkfirst=True)
        role_assignments.create(_db.engine, checkfirst=True)

        yield _db

        # Cleanup: remove session and close connections
        _db.session.remove()

        # Drop tables in reverse order
        MinecraftLocation.__table__.drop(_db.engine, checkfirst=True)
        MinecraftCommand.__table__.drop(_db.engine, checkfirst=True)
        BlogPost.__table__.drop(_db.engine, checkfirst=True)
        role_assignments.drop(_db.engine, checkfirst=True)
        Role.__table__.drop(_db.engine, checkfirst=True)
        User.__table__.drop(_db.engine, checkfirst=True)

        # Dispose of engine connections
        _db.engine.dispose()


@pytest.fixture(scope='function')
def client(app, db):
    """
    Provide a test client for making requests to the application.

    This is an unauthenticated client suitable for testing public routes.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """
    Provide a test CLI runner for testing Flask CLI commands.
    """
    return app.test_cli_runner()


# ============================================================================
# Role Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def admin_role(db):
    """Create and return an admin role."""
    role = Role(name='admin', description='Administrator role with full access')
    db.session.add(role)
    db.session.commit()
    return role


@pytest.fixture(scope='function')
def blogger_role(db):
    """Create and return a blogger role."""
    role = Role(name='blogger', description='Blogger role for creating and managing blog posts')
    db.session.add(role)
    db.session.commit()
    return role


@pytest.fixture(scope='function')
def minecrafter_role(db):
    """Create and return a minecrafter role for Minecraft server management."""
    role = Role(name='minecrafter', description='Minecraft server management role')
    db.session.add(role)
    db.session.commit()
    return role


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def regular_user(db):
    """
    Create and return a regular user without any special roles.

    Credentials:
        username: testuser
        password: password123
        email: test@example.com
    """
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def blogger_user(db, blogger_role):
    """
    Create and return a user with blogger role.

    Credentials:
        username: blogger
        password: blogpass123
        email: blogger@example.com
    """
    user = User(username='blogger', email='blogger@example.com')
    user.set_password('blogpass123')
    user.roles.append(blogger_role)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def admin_user(db, admin_role):
    """
    Create and return a user with admin role.

    Credentials:
        username: admin
        password: adminpass123
        email: admin@example.com
    """
    user = User(username='admin', email='admin@example.com')
    user.set_password('adminpass123')
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def minecrafter_user(db, minecrafter_role):
    """
    Create and return a user with minecrafter role.

    Credentials:
        username: minecrafter
        password: mcpass123
        email: minecrafter@example.com
    """
    user = User(username='minecrafter', email='minecrafter@example.com')
    user.set_password('mcpass123')
    user.roles.append(minecrafter_role)
    db.session.add(user)
    db.session.commit()
    return user


# ============================================================================
# Authenticated Client Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def auth_client(client, regular_user):
    """
    Provide a test client authenticated as a regular user.

    Automatically logs in the regular_user before test execution.
    """
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    return client


@pytest.fixture(scope='function')
def regular_client(client, regular_user):
    """
    Provide a test client authenticated as a regular user (alias for auth_client).

    Automatically logs in the regular_user before test execution.
    """
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    return client


@pytest.fixture(scope='function')
def blogger_client(client, blogger_user):
    """
    Provide a test client authenticated as a blogger.

    Automatically logs in the blogger_user before test execution.
    """
    client.post('/login', data={
        'username': 'blogger',
        'password': 'blogpass123'
    }, follow_redirects=True)
    return client


@pytest.fixture(scope='function')
def admin_client(client, admin_user):
    """
    Provide a test client authenticated as an admin.

    Automatically logs in the admin_user before test execution.
    """
    client.post('/login', data={
        'username': 'admin',
        'password': 'adminpass123'
    }, follow_redirects=True)
    return client


@pytest.fixture(scope='function')
def minecrafter_client(client, minecrafter_user):
    """
    Provide a test client authenticated as a minecrafter.

    Automatically logs in the minecrafter_user before test execution.
    """
    client.post('/login', data={
        'username': 'minecrafter',
        'password': 'mcpass123'
    }, follow_redirects=True)
    return client


# ============================================================================
# BlogPost Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def published_post(db):
    """
    Create and return a published blog post.

    Attributes:
        title: Test Published Post
        content: This is a published post.
        is_draft: False
    """
    post = BlogPost(
        title='Test Published Post',
        content='This is a published post.',
        is_draft=False,
        date_posted=datetime.now()
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture(scope='function')
def draft_post(db):
    """
    Create and return a draft blog post.

    Attributes:
        title: Test Draft Post
        content: This is a draft post.
        is_draft: True
    """
    post = BlogPost(
        title='Test Draft Post',
        content='This is a draft post.',
        is_draft=True,
        date_posted=datetime.now()
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture(scope='function')
def post_with_images(db):
    """
    Create and return a blog post with portrait and thumbnail.

    Attributes:
        title: Post with Images
        content: This post has images.
        portrait: test_portrait.jpg
        thumbnail: test_thumb.jpg
    """
    post = BlogPost(
        title='Post with Images',
        content='This post has images.',
        portrait='test_portrait.jpg',
        thumbnail='test_thumb.jpg',
        is_draft=False,
        date_posted=datetime.now()
    )
    db.session.add(post)
    db.session.commit()
    return post


# ============================================================================
# MinecraftCommand Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def sample_command(db):
    """
    Create and return a single Minecraft command for testing.

    Attributes:
        command_name: tp
        options: {"args": ["player1", "100", "64", "-200"]}
    """
    command = MinecraftCommand(
        command_name='tp',
        options={'args': ['player1', '100', '64', '-200']}
    )
    db.session.add(command)
    db.session.commit()
    return command


@pytest.fixture(scope='function')
def multiple_commands(db):
    """
    Create and return multiple Minecraft commands for list testing.

    Returns:
        list: Three MinecraftCommand objects
    """
    commands = [
        MinecraftCommand(
            command_name='tp',
            options={'args': ['player', 'x', 'y', 'z']}
        ),
        MinecraftCommand(
            command_name='give',
            options={'args': ['player', 'item', 'amount']}
        ),
        MinecraftCommand(
            command_name='weather',
            options={'args': ['clear']}
        )
    ]
    db.session.add_all(commands)
    db.session.commit()
    return commands


@pytest.fixture(scope='function')
def command_with_empty_options(db):
    """
    Create and return a command with null/empty options (edge case).

    Attributes:
        command_name: list
        options: None
    """
    command = MinecraftCommand(
        command_name='list',
        options=None
    )
    db.session.add(command)
    db.session.commit()
    return command


# ============================================================================
# CSRF Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def csrf_app():
    """
    Create a Flask app with CSRF protection ENABLED.

    Use this fixture when you need to test CSRF token handling.
    """
    import os
    # Set TESTING flag BEFORE importing create_app (before config loads)
    old_testing = os.environ.get('TESTING')
    os.environ['TESTING'] = 'true'

    from app import create_app, db as _db

    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': True,  # CSRF enabled
        'SECRET_KEY': 'test-secret-key',
        'BLOG_POST_UPLOAD_FOLDER': '/tmp/test-blog-posts',
        'PROFILE_UPLOAD_FOLDER': '/tmp/test-profiles',
        'SERVER_NAME': 'localhost.localdomain'
    }

    test_app = create_app()
    test_app.config.update(test_config)

    with test_app.app_context():
        # MinecraftCommand now uses StringArray type (JSON for SQLite, ARRAY for PostgreSQL)
        _db.create_all()
        yield test_app

        # Cleanup: remove session, drop tables, dispose connections
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()

    # Restore original TESTING flag
    if old_testing:
        os.environ['TESTING'] = old_testing
    else:
        os.environ.pop('TESTING', None)


@pytest.fixture(scope='function')
def csrf_client(csrf_app):
    """
    Provide a test client for an app with CSRF protection enabled.
    """
    return csrf_app.test_client()


def extract_csrf_token(response):
    """
    Helper function to extract CSRF token from HTML response.

    Args:
        response: Flask test response object

    Returns:
        str: CSRF token value or None if not found

    Example:
        token = extract_csrf_token(response)
        client.post('/login', data={'csrf_token': token, ...})
    """
    html = response.data.decode('utf-8')
    # Look for input with name="csrf_token"
    import re
    match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', html)
    if match:
        return match.group(1)
    return None


# ============================================================================
# Mock File Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def mock_image_file():
    """
    Create a mock image file for testing uploads.

    Returns:
        FileStorage: A mock JPEG image file

    Example:
        response = client.post('/post/new', data={
            'portrait': mock_image_file,
            'title': 'Test',
            'content': 'Content'
        })
    """
    from werkzeug.datastructures import FileStorage
    from PIL import Image

    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    return FileStorage(
        stream=img_bytes,
        filename='test_image.jpg',
        content_type='image/jpeg'
    )


@pytest.fixture(scope='function')
def mock_invalid_file():
    """
    Create a mock invalid file (non-image) for testing upload validation.

    Returns:
        FileStorage: A mock text file
    """
    from werkzeug.datastructures import FileStorage

    file_content = io.BytesIO(b'This is not an image')

    return FileStorage(
        stream=file_content,
        filename='malicious.txt',
        content_type='text/plain'
    )


# ============================================================================
# Mock RCON Fixture
# ============================================================================

@pytest.fixture(scope='function', autouse=True)
def reset_rcon_global():
    """
    Reset the global rcon variable before each test to prevent state leakage.

    This ensures that RCON tests start with a clean slate and don't interfere
    with each other due to module-level global state.
    """
    import app.routes.mc as mc_module
    original_rcon = mc_module.rcon
    mc_module.rcon = None
    yield
    mc_module.rcon = original_rcon


@pytest.fixture(scope='function')
def mock_rcon():
    """
    Mock the RCON connection for Minecraft integration tests.

    Returns:
        Mock: A mock RCON client with connect() and command() methods

    Example:
        with patch('app.routes_mc.rcon', mock_rcon):
            response = client.post('/mc/command', data={'cmd': 'list'})
    """
    mock = Mock()
    mock.connect.return_value = True
    mock.command.return_value = 'Command executed successfully'
    return mock


# ============================================================================
# Context Manager Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def app_context(app):
    """
    Provide an application context for tests that need it.

    Example:
        def test_something(app_context):
            # Code here runs inside app context
            assert current_app.config['TESTING'] is True
    """
    with app.app_context():
        yield


@pytest.fixture(scope='function')
def request_context(app):
    """
    Provide a request context for tests that need it.

    Example:
        def test_something(request_context):
            # Code here runs inside request context
            assert request.method == 'GET'
    """
    with app.test_request_context():
        yield
