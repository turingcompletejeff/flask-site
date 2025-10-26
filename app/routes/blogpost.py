from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort
import json
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from PIL import Image
from sqlalchemy.orm.attributes import flag_modified
from app import db
from app.models import BlogPost
from app.forms import BlogPostForm
from app.utils.auth_decorators import require_any_role
from app.utils.file_validation import validate_image_file, sanitize_filename
from app.utils.image_utils import delete_uploaded_images

# Create a blueprint for main routes
blogpost_bp = Blueprint('blogpost', __name__)

# Route to view a single blog post
@blogpost_bp.route('/post/<int:post_id>')
def view_post(post_id):
    # Query the specific blog post by ID
    post = db.session.get(BlogPost, post_id) or abort(404)

    # Check if post is draft and user is not authenticated
    if post.is_draft and not current_user.is_authenticated:
        flash('This post is not available.', 'error')
        return redirect(url_for('main.index'))

    return render_template('view_post.html', post=post)

# Route to create a new blog post
@blogpost_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
@require_any_role(['blogger', 'admin'])
def new_post():
    form = BlogPostForm()

    if request.method == 'GET':
        return render_template('new_post.html', form=form)

    if form.validate_on_submit():
        portrait_file = form.portrait.data
        thumbnail_file = form.thumbnail.data
        filename = None
        thumbnailname = None

        # Validate and process portrait file
        if portrait_file:
            # Security: Validate file type, size, and magic number
            current_app.logger.info(f'Portrait upload attempt by user {current_user.id}: {portrait_file.filename}')
            is_valid, error_msg = validate_image_file(portrait_file)
            if not is_valid:
                current_app.logger.warning(f'Portrait upload validation failed for user {current_user.id}: {error_msg}')
                flash(f'Portrait upload failed: {error_msg}', 'danger')
                return render_template('new_post.html', form=form)

            # Sanitize and secure the filename
            safe_filename_str = sanitize_filename(portrait_file.filename)
            filename = secure_filename(safe_filename_str)
            file_path = os.path.join(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)

            # Save original with error handling
            try:
                portrait_file.save(file_path)
                current_app.logger.info(f'Portrait saved successfully by user {current_user.id}: {filename}')
            except Exception as e:
                current_app.logger.error(f'Portrait save error for user {current_user.id}: {e}')
                flash(f'Error saving portrait image: {str(e)}', 'danger')
                return render_template('new_post.html', form=form)

        # Handle thumbnail: custom upload takes priority, otherwise auto-generate
        if thumbnail_file:
            # Security: Validate custom thumbnail file
            current_app.logger.info(f'Thumbnail upload attempt by user {current_user.id}: {thumbnail_file.filename}')
            is_valid, error_msg = validate_image_file(thumbnail_file)
            if not is_valid:
                current_app.logger.warning(f'Thumbnail upload validation failed for user {current_user.id}: {error_msg}')
                flash(f'Thumbnail upload failed: {error_msg}', 'danger')
                # Clean up portrait if it was uploaded
                if portrait_file and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        current_app.logger.info(f'Cleaned up portrait after thumbnail failure: {filename}')
                    except OSError as e:
                        current_app.logger.error(f'Failed to cleanup portrait: {e}')
                return render_template('new_post.html', form=form)

            # Custom thumbnail uploaded
            safe_thumb_name = sanitize_filename(thumbnail_file.filename)
            thumbnailname = f"custom_thumb_{secure_filename(safe_thumb_name)}"
            thumb_path = os.path.join(current_app.config['BLOG_POST_UPLOAD_FOLDER'], thumbnailname)

            # Save and resize custom thumbnail to 300x300
            try:
                thumbnail_file.save(thumb_path)
                img = Image.open(thumb_path)
                img.thumbnail((300,300))
                img.save(thumb_path)
                current_app.logger.info(f'Thumbnail saved successfully by user {current_user.id}: {thumbnailname}')
            except Exception as e:
                current_app.logger.error(f'Thumbnail processing error for user {current_user.id}: {e}')
                flash(f'Error processing thumbnail: {str(e)}', 'danger')
                # Clean up uploaded files
                if portrait_file and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        current_app.logger.info(f'Cleaned up portrait after thumbnail processing failure: {filename}')
                    except OSError as e:
                        current_app.logger.error(f'Failed to cleanup portrait: {e}')
                return render_template('new_post.html', form=form)
        elif portrait_file:
            # Auto-generate thumbnail from portrait
            thumbnailname = f"thumb_{filename}"
            thumb_path = os.path.join(
                current_app.config['BLOG_POST_UPLOAD_FOLDER'],thumbnailname
            )
            try:
                img = Image.open(file_path)
                img.thumbnail((300,300))
                img.save(thumb_path)
                current_app.logger.info(f'Auto-generated thumbnail for user {current_user.id}: {thumbnailname}')
            except Exception as e:
                current_app.logger.error(f'Thumbnail generation error for user {current_user.id}: {e}')
                flash(f'Error generating thumbnail: {str(e)}', 'danger')
                # Clean up portrait
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        current_app.logger.info(f'Cleaned up portrait after thumbnail generation failure: {filename}')
                    except OSError as e:
                        current_app.logger.error(f'Failed to cleanup portrait: {e}')
                return render_template('new_post.html', form=form)
        
        # Handle portrait resize parameters and merge with existing themap data
        themap_data = {}
        resize_params = None
        if request.form.get('portrait_resize_params'):
            try:
                resize_params = json.loads(request.form.get('portrait_resize_params'))
                themap_data['portrait_display'] = resize_params
            except (json.JSONDecodeError, TypeError):
                themap_data['portrait_display'] = {"display_mode": "auto"}
        else:
            themap_data['portrait_display'] = {"display_mode": "auto"}

        # Determine draft status based on which button was clicked
        is_draft = True  # Default to draft
        flash_message = "Draft saved!"

        if form.publish.data:
            is_draft = False
            flash_message = "Post published!"

        # create blog post object
        post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            portrait=filename,
            thumbnail=thumbnailname,
            themap=themap_data,
            is_draft=is_draft
        )

        db.session.add(post)
        db.session.commit()

        flash(flash_message, "success")
        return redirect(url_for("main.index"))

    # If form validation fails, render the form again with errors
    return render_template('new_post.html', form=form)

# Route to delete a blog post
@blogpost_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
@require_any_role(['blogger', 'admin'])
def delete_post(post_id):
    post = db.session.get(BlogPost, post_id) or abort(404)

    # Store image filenames before database deletion
    portrait = post.portrait
    thumbnail = post.thumbnail

    # Delete database record first
    db.session.delete(post)
    db.session.commit()

    # Clean up associated image files
    result = delete_uploaded_images(
        current_app.config['BLOG_POST_UPLOAD_FOLDER'],
        [portrait, thumbnail]
    )

    # Enhanced flash message based on cleanup results
    if result['errors']:
        flash(f"Post deleted, but {len(result['errors'])} image(s) could not be removed.", 'warning')
        current_app.logger.warning(f"Post {post_id} deleted with image cleanup errors: {result['errors']}")
    else:
        flash('Post and associated images deleted!', 'success')

    return redirect(url_for('main.index'))

# Route to edit an existing blog post
@blogpost_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@require_any_role(['blogger', 'admin'])
def edit_post(post_id):
    post = db.session.get(BlogPost, post_id) or abort(404)
    form = BlogPostForm()

    # Populate the form with the existing post data
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    # Update the post if the form is submitted and valid
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data

        # Determine draft status based on which button was clicked
        flash_message = "Post updated!"
        if form.save_draft.data:
            post.is_draft = True
            flash_message = "Draft saved!"
        elif form.publish.data:
            post.is_draft = False
            flash_message = "Post published!"

        # Handle portrait resize parameters and update themap data
        if request.form.get('portrait_resize_params'):
            try:
                resize_params = json.loads(request.form.get('portrait_resize_params'))
                if post.themap:
                    # Update existing themap data
                    post.themap['portrait_display'] = resize_params
                    flag_modified(post, 'themap')  # Tell SQLAlchemy the JSON field was modified
                else:
                    # Create new themap data
                    post.themap = {'portrait_display': resize_params}
            except (json.JSONDecodeError, TypeError):
                # Fallback to auto mode if JSON parsing fails
                if post.themap:
                    post.themap['portrait_display'] = {"display_mode": "auto"}
                    flag_modified(post, 'themap')  # Tell SQLAlchemy the JSON field was modified
                else:
                    post.themap = {'portrait_display': {"display_mode": "auto"}}

        db.session.commit()
        flash(flash_message, 'success')
        return redirect(url_for('blogpost.view_post', post_id=post.id))

    return render_template('edit_post.html', form=form, post=post)
