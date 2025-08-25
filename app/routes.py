from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import BlogPost
#from app.forms import BlogPostForm

# Create a blueprint for main routes
main_bp = Blueprint('main_bp', __name__)

# Home page
@main_bp.route('/')
def index():
    # Query all blog posts in descending order by date
    blog_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    
    return render_template('index.html', blog_posts=blog_posts)


@main_bp.route('/thetv')
def thetv():
    return render_template('library.html')