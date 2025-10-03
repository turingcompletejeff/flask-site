from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Role, BlogPost
from app.forms import EditUserForm, CreateUserForm, DeleteUserForm
from app.utils.pagination import paginate_query
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

# Create a blueprint for admin routes
admin_bp = Blueprint('admin_bp', __name__)

def admin_required(f):
    """Decorator to require admin role for route access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth_bp.login'))
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
        print(f"Dashboard error: {e}")
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
            return redirect(url_for('admin_bp.dashboard'))

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
            return redirect(url_for('admin_bp.dashboard'))

        # Pre-populate form
        if request.method == 'GET':
            form.username.data = user.username
            form.email.data = user.email
            form.roles.data = [r.id for r in user.roles]

        return render_template('admin_edit_user.html', form=form, user=user)

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Database error occurred while editing user.', 'danger')
        print(f"Edit user error: {e}")
        return redirect(url_for('admin_bp.dashboard'))

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
            return redirect(url_for('admin_bp.dashboard'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Database error occurred while creating user.', 'danger')
            print(f"Create user error: {e}")

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
            return redirect(url_for('admin_bp.dashboard'))

        form = DeleteUserForm()
        if form.validate_on_submit():
            username = user.username
            db.session.delete(user)
            db.session.commit()
            flash(f'User {username} deleted successfully.', 'success')
        else:
            flash('Invalid request.', 'danger')

        return redirect(url_for('admin_bp.dashboard'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Database error occurred while deleting user.', 'danger')
        print(f"Delete user error: {e}")
        return redirect(url_for('admin_bp.dashboard'))

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
