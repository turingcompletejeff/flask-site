from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required
import os
from werkzeug.utils import secure_filename
from PIL import Image
from app import db
from app.models import BlogPost
from app.forms import BlogPostForm

# Create a blueprint for main routes
blogpost_bp = Blueprint('blogpost_bp', __name__)

# Route to view a single blog post
@blogpost_bp.route('/post/<int:post_id>')
def view_post(post_id):
    # Query the specific blog post by ID
    post = BlogPost.query.get_or_404(post_id)
    return render_template('view_post.html', post=post)

# Route to create a new blog post
@blogpost_bp.route('/new', methods=['POST'])
@login_required
def new_post():
    form = BlogPostForm()
    
    if form.validate_on_submit():
        portrait_file = form.portrait.data
        filename = None
        
        if portrait_file:
            # ensure a safe filename
            filename = secure_filename(portrait_file.filename)
            file_path = os.path.join(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)
            
            # save original
            portrait_file.save(file_path)
            
            # create thumbnail
            img = Image.open(file_path)
            img.thumbnail((300,300))
            thumb_path = os.path.join(
                current_app.config['BLOG_POST_UPLOAD_FOLDER'],f"thumb_{filename}"
            )
            img.save(thumb_path)
        
        # create blog post object
        post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            portrait=filename,
            thumbnail=f"thumb_{filename}"
        )
        
        db.session.add(post)
        db.session.commit()

        flash("post created!", "success")
        return redirect(url_for("main_bp.index"))
    
    print(form.errors)
    flash("post invalid","error")
    return redirect(url_for("main_bp.index"))
