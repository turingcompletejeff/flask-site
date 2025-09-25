from app import db
from datetime import date, datetime, timezone
from sqlalchemy.dialects.postgresql import ARRAY
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
