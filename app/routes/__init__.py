"""Route blueprints for flask-site application."""
from .main import main_bp
from .auth import auth_bp
from .blogpost import blogpost_bp
from .mc import mc_bp
from .mc_commands import mc_commands_bp
from .admin import admin_bp
from .health import health_bp
from .profile import profile_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'blogpost_bp',
    'mc_bp',
    'mc_commands_bp',
    'admin_bp',
    'health_bp',
    'profile_bp',
]
