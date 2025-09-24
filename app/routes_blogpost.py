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
@blogpost_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = BlogPostForm()

    if request.method == 'GET':
        return render_template('new_post.html', form=form)

    if form.validate_on_submit():
        portrait_file = form.portrait.data
        filename = None
        thumbnailname = None
        
        if portrait_file:
            # ensure a safe filename
            filename = secure_filename(portrait_file.filename)
            file_path = os.path.join(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)
            
            # save original
            portrait_file.save(file_path)
            
            # create thumbnail
            thumbnailname = f"thumb_{filename}"
            img = Image.open(file_path)
            img.thumbnail((300,300))
            thumb_path = os.path.join(
                current_app.config['BLOG_POST_UPLOAD_FOLDER'],thumbnailname
            )
            img.save(thumb_path)
        
        # create blog post object
        post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            portrait=filename,
            thumbnail=thumbnailname
        )
        
        db.session.add(post)
        db.session.commit()

        flash("post created!", "success")
        return redirect(url_for("main_bp.index"))

    # If form validation fails, render the form again with errors
    return render_template('new_post.html', form=form)

# Route to delete a blog post
@blogpost_bp.route('/post/delete', methods=['POST'])
@login_required
def delete_post():
    post_id = request.form.get("id")
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('post deleted!', 'success')
    return redirect(url_for('main_bp.index'))

# Route to edit an existing blog post
@blogpost_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm()

    # Populate the form with the existing post data
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    # Update the post if the form is submitted and valid
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('post updated!', 'success')
        return redirect(url_for('blogpost_bp.view_post', post_id=post.id))

    return render_template('edit_post.html', form=form, post=post)
