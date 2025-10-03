from app import db
from datetime import date, datetime, timezone
from sqlalchemy.dialects.postgresql import ARRAY
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

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'  # Optional: specify the table name in the database

    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each blog post
    title = db.Column(db.Text, nullable=False)  # Title of the blog post
    content = db.Column(db.Text, nullable=False)  # Content of the blog post
    thumbnail = db.Column(db.Text, nullable=True)  # URI to the thumbnail of the blog post
    portrait = db.Column(db.Text, nullable=True) # URI to the portrait (larger pic) for the blog post
    themap = db.Column(db.JSON, nullable=True) # general use JSON map
    date_posted = db.Column(db.Date, nullable=False, default=datetime.now)  # Creation date
    last_updated = db.Column(db.DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))  # Last update date -- always store UTC
    is_draft = db.Column(db.Boolean, nullable=False, default=True)  # Draft status

    def __repr__(self):
        return f'<BlogPost {self.title}>'

    def hasEdits(self):
        return self.last_updated is not None

class MinecraftCommand(db.Model):
    __tablename__ = 'minecraft_commands'
    
    command_id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(20), nullable=True)
    options = db.Column(ARRAY(db.String(40)))
    
    def __repr__(self):
        return f'<BlogPost {self.command_name}>'
    
    def to_dict(self):
        return {
            'command_id': self.command_id,
            'command_name': self.command_name,
            'options': self.options
        }
