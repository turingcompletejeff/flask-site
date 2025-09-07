from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from app import db
from app.models import BlogPost
#from app.forms import BlogPostForm

# Create a blueprint for main routes
main_bp = Blueprint('main_bp', __name__)

# Home page
@main_bp.route('/')
def index():
    msg = request.args.get("flash")
    cat = request.args.get("category", "info")
    if msg:
        flash(msg, cat)
    # Query all blog posts in descending order by date
    blog_posts = BlogPost.query.order_by(BlogPost.date_posted.desc(),BlogPost.id.desc()).all()
    
    return render_template('index.html', blog_posts=blog_posts, current_page="blog")

# About page
@main_bp.route('/about')
def about():
    return render_template('about.html', current_page="about")
    
# Contact form
@main_bp.route('/contact')
def about():
    return render_template('contact.html', current_page="contact")

@main_bp.route('/uploads/blog-posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)
