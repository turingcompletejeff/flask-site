"""
Authorization decorators for role-based access control.
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def require_role(role_name):
    """
    Decorator to require a specific role for accessing a route.

    Args:
        role_name (str): The name of the required role

    Returns:
        The decorated function

    Raises:
        401: If user is not authenticated
        403: If user doesn't have the required role

    Note:
        Admin users bypass all role checks and can access any route.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized

            # Admin bypass - admins can access everything
            if current_user.is_admin():
                return f(*args, **kwargs)

            if not current_user.has_role(role_name):
                abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_role(role_names):
    """
    Decorator to require any of the specified roles for accessing a route.

    Args:
        role_names (list): List of role names, user must have at least one

    Returns:
        The decorated function

    Raises:
        401: If user is not authenticated
        403: If user doesn't have any of the required roles

    Note:
        Admin users bypass all role checks and can access any route.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized

            # Admin bypass
            if current_user.is_admin():
                return f(*args, **kwargs)

            if not current_user.has_any_role(role_names):
                abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator
