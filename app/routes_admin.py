from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Role

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
    # Get all users with their roles
    users = User.query.order_by(User.created_at.desc()).all()

    return render_template('admin_dashboard.html', users=users, current_page='admin')
