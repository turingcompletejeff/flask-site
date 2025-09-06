from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from app import db
from app.models import BlogPost
#from app.forms import BlogPostForm

# Create a blueprint for main routes
main_bp = Blueprint('main_bp', __name__)

# Home page
@main_bp.route('/')
def index():
    # Query all blog posts in descending order by date
    blog_posts = BlogPost.query.order_by(BlogPost.date_posted.desc(),BlogPost.id.desc()).all()
    
    return render_template('index.html', blog_posts=blog_posts, current_page="blog")


@main_bp.route('/uploads/blog-posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)
