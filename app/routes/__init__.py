"""Route blueprints for flask-site application."""
from .main import main
from .auth import auth
from .blogpost import blogpost
from .mc import mc
from .admin import admin
from .health import health
from .profile import profile

__all__ = [
    'main',
    'auth',
    'blogpost',
    'mc',
    'admin',
    'health',
    'profile',
]
