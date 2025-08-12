from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models import BlogPost

# Create a blueprint for main routes
blogpost_bp = Blueprint('blogpost_bp', __name__)

# Route to view a single blog post
@blogpost_bp.route('/post/<int:post_id>')
def view_post(post_id):
    # Query the specific blog post by ID
    post = BlogPost.query.get_or_404(post_id)
    return render_template('view_post.html', post=post)