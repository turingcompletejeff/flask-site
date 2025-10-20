"""Forms for flask-site application."""
from .contact import ContactForm
from .blog import BlogPostForm
from .profile import ProfileEditForm, PasswordChangeForm
from .admin import EditUserForm, CreateUserForm, DeleteUserForm, CreateRoleForm, EditRoleForm, DeleteRoleForm

__all__ = [
    'ContactForm',
    'BlogPostForm',
    'ProfileEditForm',
    'PasswordChangeForm',
    'EditUserForm',
    'CreateUserForm',
    'DeleteUserForm',
    'CreateRoleForm',
    'EditRoleForm',
    'DeleteRoleForm',
]
