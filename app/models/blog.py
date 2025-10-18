from app import db
from datetime import datetime, timezone


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
