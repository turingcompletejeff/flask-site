from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Role, BlogPost
from app.forms import EditUserForm, CreateUserForm, DeleteUserForm
from app.utils.pagination import paginate_query
from app.utils.image_utils import delete_uploaded_images
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import os
from pathlib import Path

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin role for route access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Admin access required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with user management widget"""
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 10

        # Get users with pagination
        users_query = User.query.order_by(User.created_at.desc())
        users, total_pages, current_page, has_prev, has_next = paginate_query(users_query, page, per_page)

        # Get all roles for inline toggle
        all_roles = Role.query.order_by(Role.name).all()

        # Calculate statistics
        total_users = User.query.count()
        total_admins = User.query.filter(User.roles.any(Role.name == 'admin')).count()
        total_posts = BlogPost.query.count()

        # Users created this month
        one_month_ago = datetime.now(timezone.utc) - relativedelta(months=1)
        users_this_month = User.query.filter(User.created_at >= one_month_ago).count()

        stats = {
            'total_users': total_users,
            'total_admins': total_admins,
            'total_posts': total_posts,
            'users_this_month': users_this_month
        }

        return render_template('admin_dashboard.html',
                             users=users,
                             all_roles=all_roles,
                             stats=stats,
                             current_page=current_page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             page='admin')

    except SQLAlchemyError as e:
        flash('Database error occurred while loading dashboard.', 'danger')
        current_app.logger.error(f"Dashboard error: {e}")
        return render_template('admin_dashboard.html',
                             users=[],
                             stats={'total_users': 0, 'total_admins': 0, 'total_posts': 0, 'users_this_month': 0},
                             current_page=1,
                             total_pages=1,
                             has_prev=False,
                             has_next=False,
                             page='admin')

@admin_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user information"""
    try:
        user = User.query.get_or_404(user_id)

        # Prevent editing self
        if user.id == current_user.id:
            flash('You cannot edit your own account from here. Use your profile page.', 'warning')
            return redirect(url_for('admin.dashboard'))

        # Get all available roles
        all_roles = Role.query.order_by(Role.name).all()
        form = EditUserForm()
        form.roles.choices = [(r.id, r.name) for r in all_roles]

        if form.validate_on_submit():
            # Check if username is unique (excluding current user)
            existing_user = User.query.filter(User.username == form.username.data, User.id != user_id).first()
            if existing_user:
                flash('Username already exists.', 'danger')
                return render_template('admin_edit_user.html', form=form, user=user)

            # Check if email is unique (excluding current user)
            existing_email = User.query.filter(User.email == form.email.data, User.id != user_id).first()
            if existing_email:
                flash('Email already exists.', 'danger')
                return render_template('admin_edit_user.html', form=form, user=user)

            user.username = form.username.data
            user.email = form.email.data

            # Update roles
            selected_role_ids = form.roles.data

            # Security check: Prevent removing last admin
            admin_role = Role.query.filter_by(name='admin').first()
            if user.has_role('admin') and admin_role and admin_role.id not in selected_role_ids:
                admin_count = User.query.join(User.roles).filter(Role.name == 'admin').count()
                if admin_count <= 1:
                    flash('Cannot remove admin role from the last admin user.', 'danger')
                    return render_template('admin_edit_user.html', form=form, user=user)

            # Clear and reassign roles
            user.roles = []
            for role_id in selected_role_ids:
                role = Role.query.get(role_id)
                if role:
                    user.roles.append(role)

            db.session.commit()

            flash(f'User {user.username} updated successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

        # Pre-populate form
        if request.method == 'GET':
            form.username.data = user.username
            form.email.data = user.email
            form.roles.data = [r.id for r in user.roles]

        return render_template('admin_edit_user.html', form=form, user=user)

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Database error occurred while editing user.', 'danger')
        current_app.logger.error(f"Edit user error: {e}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    form = CreateUserForm()

    if form.validate_on_submit():
        try:
            # Check if username exists
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already exists.', 'danger')
                return render_template('admin_create_user.html', form=form)

            # Check if email exists
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Email already exists.', 'danger')
                return render_template('admin_create_user.html', form=form)

            # Create new user
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            flash(f'User {user.username} created successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Database error occurred while creating user.', 'danger')
            current_app.logger.error(f"Create user error: {e}")

    return render_template('admin_create_user.html', form=form)

@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    try:
        user = User.query.get_or_404(user_id)

        # Prevent deleting self
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('admin.dashboard'))

        form = DeleteUserForm()
        if form.validate_on_submit():
            username = user.username

            # Store profile image filenames before database deletion
            # Pattern: {user_id}_thumb.png and {user_id}_profile.png
            profile_images = []
            if user.profile_picture:
                # User.profile_picture stores the thumbnail filename
                profile_images.append(user.profile_picture)

                # Also delete the corresponding original profile picture
                # Pattern: X_thumb.png -> X_profile.png
                thumb_filename = user.profile_picture
                if '_thumb.' in thumb_filename:
                    original_filename = thumb_filename.replace('_thumb.', '_profile.')
                    profile_images.append(original_filename)

            # Delete database record first
            db.session.delete(user)
            db.session.commit()

            # Clean up associated profile image files
            if profile_images:
                result = delete_uploaded_images(
                    current_app.config['PROFILE_UPLOAD_FOLDER'],
                    profile_images
                )

                # Enhanced flash message based on cleanup results
                if result['errors']:
                    flash(f"User {username} deleted, but {len(result['errors'])} image(s) could not be removed.", 'warning')
                    current_app.logger.warning(f"User {user_id} deleted with image cleanup errors: {result['errors']}")
                else:
                    flash(f'User {username} and associated images deleted successfully.', 'success')
            else:
                flash(f'User {username} deleted successfully.', 'success')
        else:
            flash('Invalid request.', 'danger')

        return redirect(url_for('admin.dashboard'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Database error occurred while deleting user.', 'danger')
        current_app.logger.error(f"Delete user error: {e}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/users/<int:user_id>/toggle-role/<role_name>', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id, role_name):
    """Toggle a role for a user via AJAX"""
    try:
        user = User.query.get_or_404(user_id)
        role = Role.query.filter_by(name=role_name).first_or_404()

        has_role = user.has_role(role_name)

        # Security: Prevent removing last admin
        if has_role and role_name == 'admin':
            admin_count = User.query.join(User.roles).filter(Role.name == 'admin').count()
            if admin_count <= 1:
                return jsonify({
                    'success': False,
                    'error': 'Cannot remove the last admin user'
                }), 400

        # Security: Prevent self-demotion
        if user.id == current_user.id and has_role and role_name == 'admin':
            return jsonify({
                'success': False,
                'error': 'Cannot remove your own admin role'
            }), 400

        # Toggle role
        if has_role:
            user.roles.remove(role)
        else:
            user.roles.append(role)

        db.session.commit()

        return jsonify({
            'success': True,
            'has_role': not has_role,
            'role': role_name
        })

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500

@admin_bp.route('/admin/images')
@login_required
@admin_required
def manage_images():
    """
    Image management widget - view and manage all uploaded images.

    Scans configured directories for image files and checks their usage
    in the database (BlogPost, User models) and templates/CSS files.

    Returns:
        Rendered admin_images.html template with:
            - images_by_directory: Dict of directory -> list of file info
            - stats: Statistics (total images, orphaned count, sizes)

    Requires:
        - User must be authenticated (@login_required)
        - User must have admin role (@admin_required)

    Scanned directories:
        - uploads/* (all subdirectories)
        - app/static/img
    """
    try:
        images_by_directory = {}

        # Define directories to scan
        scan_directories = [
            ('uploads', 'Uploads'),  # Will scan subdirectories
            ('app/static/img', 'Static Images')  # Single directory
        ]

        # Scan uploads subdirectories
        uploads_dir = Path('uploads')
        if uploads_dir.exists():
            for subdir in uploads_dir.iterdir():
                if subdir.is_dir():
                    dir_name = f"uploads/{subdir.name}"
                    images_by_directory[dir_name] = []

                    # List all image files in this directory
                    for image_file in subdir.iterdir():
                        if image_file.is_file():
                            file_stat = image_file.stat()
                            file_info = {
                                'filename': image_file.name,
                                'path': str(image_file),
                                'size': file_stat.st_size,
                                'size_kb': round(file_stat.st_size / 1024, 2),
                                'modified': datetime.fromtimestamp(file_stat.st_mtime),
                                'in_use': False,
                                'used_by': []
                            }
                            images_by_directory[dir_name].append(file_info)

        # Scan app/static/img directory
        static_img_dir = Path('app/static/img')
        if static_img_dir.exists():
            dir_name = 'app/static/img'
            images_by_directory[dir_name] = []

            for image_file in static_img_dir.iterdir():
                if image_file.is_file() and not image_file.name.startswith('.'):
                    file_stat = image_file.stat()
                    file_info = {
                        'filename': image_file.name,
                        'path': str(image_file),
                        'size': file_stat.st_size,
                        'size_kb': round(file_stat.st_size / 1024, 2),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime),
                        'in_use': False,
                        'used_by': []
                    }
                    images_by_directory[dir_name].append(file_info)

        # Check database for image usage
        # Check BlogPost table for blog-posts directory
        if 'uploads/blog-posts' in images_by_directory:
            blog_posts = BlogPost.query.all()
            for post in blog_posts:
                for image_info in images_by_directory['uploads/blog-posts']:
                    filename = image_info['filename']
                    # Check both portrait and thumbnail fields
                    if post.portrait and filename in post.portrait:
                        image_info['in_use'] = True
                        image_info['used_by'].append(f'Post #{post.id}: {post.title}')
                    if post.thumbnail and filename in post.thumbnail:
                        image_info['in_use'] = True
                        if f'Post #{post.id}: {post.title}' not in image_info['used_by']:
                            image_info['used_by'].append(f'Post #{post.id}: {post.title}')

        # Check User table for profiles directory
        if 'uploads/profiles' in images_by_directory:
            users = User.query.all()
            for user in users:
                for image_info in images_by_directory['uploads/profiles']:
                    filename = image_info['filename']
                    # Check if this is the thumbnail stored in database
                    if user.profile_picture and filename in user.profile_picture:
                        image_info['in_use'] = True
                        image_info['used_by'].append(f'User #{user.id}: {user.username}')

                        # Also mark the corresponding original profile picture as in use
                        # Pattern: X_thumb.png -> X_profile.png
                        if '_thumb.' in filename:
                            original_filename = filename.replace('_thumb.', '_profile.')
                            for orig_info in images_by_directory['uploads/profiles']:
                                if orig_info['filename'] == original_filename:
                                    orig_info['in_use'] = True
                                    orig_info['used_by'].append(f'User #{user.id}: {user.username} (original)')
                                    break

        # Scan static images usage in templates and CSS files
        if 'app/static/img' in images_by_directory:
            # Scan all template files
            template_dir = Path('app/templates')
            static_css_dir = Path('app/static/css')

            for image_info in images_by_directory['app/static/img']:
                filename = image_info['filename']

                # Search in templates
                if template_dir.exists():
                    for template_file in template_dir.rglob('*.html'):
                        try:
                            content = template_file.read_text()
                            if filename in content:
                                image_info['in_use'] = True
                                image_info['used_by'].append(f'Template: {template_file.name}')
                        except Exception:
                            pass

                # Search in CSS files
                if static_css_dir.exists():
                    for css_file in static_css_dir.rglob('*.css'):
                        try:
                            content = css_file.read_text()
                            if filename in content:
                                image_info['in_use'] = True
                                if f'CSS: {css_file.name}' not in image_info['used_by']:
                                    image_info['used_by'].append(f'CSS: {css_file.name}')
                        except Exception:
                            pass

                # If no usage found, mark as potentially orphaned
                if not image_info['in_use']:
                    image_info['used_by'].append('⚠️ Not found in templates or CSS')

        # Calculate statistics
        total_images = sum(len(images) for images in images_by_directory.values())
        total_orphaned = sum(1 for images in images_by_directory.values() for img in images if not img['in_use'])
        total_size_kb = sum(img['size_kb'] for images in images_by_directory.values() for img in images)
        orphaned_size_kb = sum(img['size_kb'] for images in images_by_directory.values() for img in images if not img['in_use'])

        stats = {
            'total_images': total_images,
            'total_orphaned': total_orphaned,
            'total_size_mb': round(total_size_kb / 1024, 2),
            'orphaned_size_mb': round(orphaned_size_kb / 1024, 2)
        }

        return render_template('admin_images.html',
                             images_by_directory=images_by_directory,
                             stats=stats,
                             page='admin')

    except Exception as e:
        flash('Error loading image management.', 'danger')
        current_app.logger.error(f"Image management error: {e}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/images/delete/<path:image_path>', methods=['POST'])
@login_required
@admin_required
def delete_image(image_path):
    """
    Delete a specific image file with comprehensive security validation.

    Args:
        image_path: Relative path to the image file

    Returns:
        Redirect to manage_images page with success or error message

    Security:
        - Validates path against traversal attacks
        - Ensures file is within allowed directories
        - Logs all deletion attempts for audit trail
    """
    # Log deletion attempt for security audit
    current_app.logger.info(f'Image deletion requested by user {current_user.id} ({current_user.username}): {image_path}')

    try:
        # Security: Strict path validation - reject any path traversal attempts
        # Check for various path traversal patterns
        dangerous_patterns = ['..', '~', '//', '\\\\', '\x00']
        if any(pattern in image_path for pattern in dangerous_patterns):
            current_app.logger.warning(f'Path traversal attempt detected by user {current_user.id}: {image_path}')
            flash('Invalid image path detected.', 'danger')
            return redirect(url_for('admin.manage_images'))

        # Reject absolute paths
        if image_path.startswith('/') or (len(image_path) > 1 and image_path[1] == ':'):
            current_app.logger.warning(f'Absolute path rejected for user {current_user.id}: {image_path}')
            flash('Invalid image path detected.', 'danger')
            return redirect(url_for('admin.manage_images'))

        # Ensure the path is within allowed directories
        allowed_prefixes = ['uploads/', 'app/static/img/']
        if not any(image_path.startswith(prefix) for prefix in allowed_prefixes):
            current_app.logger.warning(f'Path outside allowed directories for user {current_user.id}: {image_path}')
            flash('Invalid image path.', 'danger')
            return redirect(url_for('admin.manage_images'))

        file_path = Path(image_path)

        # Security check: resolve path and ensure it's still in allowed directory
        try:
            resolved_path = file_path.resolve(strict=True)
            allowed_dirs = [Path('uploads').resolve(), Path('app/static/img').resolve()]

            # Verify resolved path is within allowed directories
            is_within_allowed = False
            for allowed_dir in allowed_dirs:
                try:
                    resolved_path.relative_to(allowed_dir)
                    is_within_allowed = True
                    break
                except ValueError:
                    continue

            if not is_within_allowed:
                current_app.logger.warning(f'Resolved path outside allowed directories for user {current_user.id}: {resolved_path}')
                flash('Invalid image path.', 'danger')
                return redirect(url_for('admin.manage_images'))
        except (OSError, RuntimeError) as e:
            current_app.logger.error(f'Path resolution failed for user {current_user.id}, path {image_path}: {e}')
            flash('Invalid image path.', 'danger')
            return redirect(url_for('admin.manage_images'))

        # Security check: ensure file exists and is a file
        if not file_path.exists():
            current_app.logger.warning(f'File not found for deletion by user {current_user.id}: {image_path}')
            flash('Image not found.', 'danger')
            return redirect(url_for('admin.manage_images'))

        if not file_path.is_file():
            current_app.logger.warning(f'Attempted to delete non-file by user {current_user.id}: {image_path}')
            flash('Invalid file path.', 'danger')
            return redirect(url_for('admin.manage_images'))

        # Get file info for logging before deletion
        file_size = file_path.stat().st_size
        file_name = file_path.name

        # Delete the file with error handling
        try:
            os.remove(file_path)
            current_app.logger.info(f'Image deleted successfully by user {current_user.id}: {image_path} ({file_size} bytes)')
            flash(f'Image {file_name} deleted successfully.', 'success')
        except PermissionError as e:
            current_app.logger.error(f'Permission denied deleting image for user {current_user.id}: {image_path} - {e}')
            flash('Permission denied: Unable to delete image.', 'danger')
        except OSError as e:
            current_app.logger.error(f'OS error deleting image for user {current_user.id}: {image_path} - {e}')
            flash(f'Error deleting image: {str(e)}', 'danger')

    except Exception as e:
        current_app.logger.error(f'Unexpected error during image deletion for user {current_user.id}: {image_path} - {e}')
        flash('An unexpected error occurred while deleting the image.', 'danger')

    return redirect(url_for('admin.manage_images'))

@admin_bp.route('/admin/images/purge-orphaned', methods=['POST'])
@login_required
@admin_required
def purge_orphaned_images():
    """
    Delete all orphaned images (not referenced in database).

    Scans uploads directory and removes files that are not referenced
    in any database model (BlogPost, User).

    Returns:
        Redirect to manage_images with success/error message

    Requires:
        - User must be authenticated (@login_required)
        - User must have admin role (@admin_required)

    Security:
        - Only processes files in uploads directory
        - Skips files referenced in BlogPost.portrait, BlogPost.thumbnail
        - Skips files referenced in User.profile_picture
        - Protects both thumbnail and original profile pictures
    """
    try:
        uploads_dir = Path('uploads')
        deleted_count = 0
        deleted_size_kb = 0
        errors = []

        # Get all images in use from database (optimized - single query per table)
        images_in_use = set()

        # From BlogPost - get all at once
        blog_posts = BlogPost.query.all()
        for post in blog_posts:
            if post.portrait:
                images_in_use.add(os.path.basename(post.portrait))
            if post.thumbnail:
                images_in_use.add(os.path.basename(post.thumbnail))

        # From User - get all at once
        users = User.query.all()
        for user in users:
            if user.profile_picture:
                thumb_filename = os.path.basename(user.profile_picture)
                images_in_use.add(thumb_filename)

                # Also protect the corresponding original profile picture
                # Pattern: X_thumb.png -> X_profile.png
                if '_thumb.' in thumb_filename:
                    original_filename = thumb_filename.replace('_thumb.', '_profile.')
                    images_in_use.add(original_filename)

        # Scan and delete orphaned files
        if uploads_dir.exists():
            for subdir in uploads_dir.iterdir():
                if subdir.is_dir():
                    for image_file in subdir.iterdir():
                        if image_file.is_file():
                            # Re-check just before deletion to minimize race condition
                            filename = image_file.name
                            if filename not in images_in_use:
                                try:
                                    file_size = image_file.stat().st_size
                                    os.remove(image_file)
                                    deleted_count += 1
                                    deleted_size_kb += file_size / 1024
                                except OSError as e:
                                    errors.append(f'{filename}: {str(e)}')

        # Report results
        if deleted_count > 0:
            flash(f'Purged {deleted_count} orphaned images ({round(deleted_size_kb / 1024, 2)} MB freed).', 'success')
        else:
            flash('No orphaned images found to purge.', 'info')

        if errors:
            flash(f'Errors occurred while deleting {len(errors)} file(s).', 'warning')
            for error in errors[:5]:  # Show first 5 errors
                current_app.logger.warning(f"Purge error: {error}")

    except Exception as e:
        flash(f'Error purging orphaned images: {str(e)}', 'danger')
        current_app.logger.error(f"Purge orphaned images error: {e}")

    return redirect(url_for('admin.manage_images'))

@admin_bp.route('/admin/roles')
@login_required
@admin_required
def roles():
    """
    Role management page - view and edit all roles and their badge colors.

    Displays a table of all roles with their properties:
    - Name
    - Description
    - Badge color (with live preview)
    - Edit capabilities

    Returns:
        Rendered admin_roles.html template with all roles

    Requires:
        - User must be authenticated (@login_required)
        - User must have admin role (@admin_required)
    """
    try:
        # Get all roles ordered by name
        all_roles = Role.query.order_by(Role.name).all()

        return render_template('admin_roles.html',
                             roles=all_roles,
                             page='admin')

    except SQLAlchemyError as e:
        flash('Database error occurred while loading roles.', 'danger')
        current_app.logger.error(f"Roles management error: {e}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/update_role_badge', methods=['POST'])
@login_required
@admin_required
def update_role_badge():
    """
    Update a role's badge color via AJAX.

    Expects JSON payload:
        {
            'role_id': int,
            'badge_color': str (hex color code)
        }

    Returns:
        JSON response:
            Success: {'status': 'success', 'badge_color': str}
            Error: {'status': 'error', 'message': str}

    Requires:
        - User must be authenticated (@login_required)
        - User must have admin role (@admin_required)
        - Valid hex color code format

    Security:
        - Validates hex color format server-side
        - Prevents SQL injection through ORM
        - Returns 404 for non-existent roles
        - Returns 400 for invalid color formats
    """
    try:
        # Get JSON data
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        role_id = data.get('role_id')
        badge_color = data.get('badge_color')

        # Validate required fields
        if not role_id or not badge_color:
            return jsonify({
                'status': 'error',
                'message': 'Missing role_id or badge_color'
            }), 400

        # Get the role
        role = Role.query.get(role_id)
        if not role:
            return jsonify({
                'status': 'error',
                'message': 'Role not found'
            }), 404

        # Validate hex color format
        if not Role.validate_hex_color(badge_color):
            return jsonify({
                'status': 'error',
                'message': 'Invalid hex color format. Use #RGB or #RRGGBB format.'
            }), 400

        # Capture old color for audit logging
        old_color = role.badge_color

        # Update badge color
        role.badge_color = badge_color
        db.session.commit()

        # Enhanced audit logging with old → new color change
        current_app.logger.info(
            f"Role '{role.name}' badge color updated from {old_color} to {badge_color} "
            f"by user {current_user.id} ({current_user.username})"
        )

        return jsonify({
            'status': 'success',
            'badge_color': badge_color
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating role badge color: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Database error occurred'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error updating role badge color: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
