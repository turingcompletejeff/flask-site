from app import db
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# Association table for many-to-many relationship between users and roles
role_assignments = db.Table('role_assignments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    badge_color = db.Column(db.String(7), nullable=False, default=lambda: '#58cc02')

    def __init__(self, **kwargs):
        """Initialize Role with default badge_color if not provided."""
        if 'badge_color' not in kwargs:
            kwargs['badge_color'] = '#58cc02'
        super(Role, self).__init__(**kwargs)

    @classmethod
    def validate_hex_color(cls, color):
        """Validate hex color code format."""
        if color is None or not isinstance(color, str):
            return False
        import re
        return bool(re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color))

    def __repr__(self):
        return f'<Role {self.name}>'


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    profile_picture = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationship to roles
    roles = db.relationship('Role', secondary=role_assignments, backref='assigned_users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Check if user has a specific role"""
        return any(r.name == role_name for r in self.roles)

    def has_any_role(self, role_names):
        """Check if user has any of the specified roles"""
        user_role_names = {r.name for r in self.roles}
        return bool(user_role_names.intersection(set(role_names)))

    def is_admin(self):
        """Check if user is an admin"""
        return self.has_role('admin')
