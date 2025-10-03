from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
import os
from app import db
from app.models import User
from app.forms import ProfileEditForm, PasswordChangeForm

# Create a blueprint for profile routes
profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/profile')
@login_required
def view_profile():
    """Display user profile"""
    return render_template('profile.html', user=current_user)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile information"""
    form = ProfileEditForm()

    if request.method == 'GET':
        # Pre-populate form with current user data
        form.email.data = current_user.email
        form.bio.data = current_user.bio

    if form.validate_on_submit():
        # Update email
        current_user.email = form.email.data

        # Update bio
        current_user.bio = form.bio.data

        # Handle profile picture upload
        if form.profile_picture.data:
            profile_picture_file = form.profile_picture.data

            # Get file extension
            file_extension = secure_filename(profile_picture_file.filename).rsplit('.', 1)[1].lower()

            # Create filenames
            filename = f"{current_user.id}_profile.{file_extension}"
            thumbnailname = f"{current_user.id}_thumb.{file_extension}"

            # Save original
            file_path = os.path.join(current_app.config['PROFILE_UPLOAD_FOLDER'], filename)
            profile_picture_file.save(file_path)

            # Create thumbnail (200x200)
            img = Image.open(file_path)
            img.thumbnail((200, 200))
            thumb_path = os.path.join(current_app.config['PROFILE_UPLOAD_FOLDER'], thumbnailname)
            img.save(thumb_path)

            # Store thumbnail name in database
            current_user.profile_picture = thumbnailname

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile_bp.view_profile'))

    return render_template('edit_profile.html', form=form)

@profile_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = PasswordChangeForm()

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('profile_bp.change_password'))

        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash('Password changed successfully!', 'success')
        return redirect(url_for('profile_bp.view_profile'))

    return render_template('change_password.html', form=form)

@profile_bp.route('/uploads/profiles/<filename>')
def profile_picture(filename):
    """Serve profile picture files"""
    return send_from_directory(current_app.config['PROFILE_UPLOAD_FOLDER'], filename)
