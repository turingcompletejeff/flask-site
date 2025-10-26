"""
Minecraft Commands Management Blueprint (TC-50)

Provides CRUD operations for managing Minecraft RCON command templates
with inline editing capabilities.

Routes:
- GET  /mc/commands                         - List/management page
- POST /mc/commands/create                  - Create command (AJAX)
- POST /mc/commands/<int:command_id>/update - Update command (AJAX)
- POST /mc/commands/<int:command_id>/delete - Delete command (form POST)

Authentication:
- Requires login (blueprint-level @before_request)
- Requires minecrafter role OR admin role
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import MinecraftCommand
from app.forms import DeleteMinecraftCommandForm

# Create blueprint
mc_commands_bp = Blueprint('mc_commands', __name__)


@mc_commands_bp.before_request
def require_login_and_role():
    """
    Require authentication and minecrafter/admin role for all routes.

    Applied to all routes in this blueprint automatically.
    Admin role bypasses minecrafter role requirement.
    """
    if not current_user.is_authenticated:
        flash("You must be logged in to access this page.", "warning")
        return redirect(url_for('auth.login'))

    # Check for minecrafter role or admin bypass
    if not current_user.is_admin() and not current_user.has_role('minecrafter'):
        abort(403)  # Forbidden


@mc_commands_bp.route('/mc/commands')
def list_commands():
    """
    GET - Render command management page with all commands.

    Returns:
        Rendered template with commands list

    Template context:
        - commands: List of all MinecraftCommand objects
        - current_page: 'minecraft' (for navigation highlighting)
    """
    try:
        commands = MinecraftCommand.query.order_by(MinecraftCommand.command_id.asc()).all()
        return render_template('mc_commands.html', commands=commands, current_page='minecraft')

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error loading commands: {e}")
        flash('Error loading commands.', 'danger')
        return render_template('mc_commands.html', commands=[], current_page='minecraft')


@mc_commands_bp.route('/mc/commands/create', methods=['POST'])
def create_command():
    """
    POST - Create new command via AJAX (JSON).

    Expects JSON payload:
        {
            "command_name": str (required, 1-20 chars, unique),
            "options": dict|null (optional, must be JSON object if provided)
        }

    Returns:
        JSON response:
            Success (201): {
                "status": "success",
                "command": {
                    "command_id": int,
                    "command_name": str,
                    "options": dict|null
                }
            }
            Error (400): {
                "status": "error",
                "message": str
            }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        # Validate command_name
        command_name = data.get('command_name', '').strip()

        if not command_name:
            return jsonify({
                'status': 'error',
                'message': 'Command name is required'
            }), 400

        if len(command_name) > 20:
            return jsonify({
                'status': 'error',
                'message': 'Command name must not exceed 20 characters'
            }), 400

        # Check for duplicate name
        existing_command = MinecraftCommand.query.filter_by(command_name=command_name).first()
        if existing_command:
            return jsonify({
                'status': 'error',
                'message': f'Command "{command_name}" already exists'
            }), 400

        # Validate options (must be dict if provided)
        options = data.get('options')
        if options is not None and not isinstance(options, dict):
            return jsonify({
                'status': 'error',
                'message': 'Options must be a JSON object'
            }), 400

        # Create command
        command = MinecraftCommand(
            command_name=command_name,
            options=options
        )
        db.session.add(command)
        db.session.commit()

        # Audit logging
        current_app.logger.info(
            f"Command '{command_name}' created by user {current_user.id} ({current_user.username})"
        )

        return jsonify({
            'status': 'success',
            'command': {
                'command_id': command.command_id,
                'command_name': command.command_name,
                'options': command.options
            }
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error creating command: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Database error occurred'
        }), 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error creating command: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500


@mc_commands_bp.route('/mc/commands/<int:command_id>/update', methods=['POST'])
def update_command(command_id):
    """
    POST - Update existing command via AJAX (JSON).

    Args:
        command_id: Command ID from URL parameter

    Expects JSON payload:
        {
            "command_name": str (required, 1-20 chars),
            "options": dict|null (optional)
        }

    Returns:
        JSON response:
            Success (200): {
                "status": "success",
                "command": {
                    "command_id": int,
                    "command_name": str,
                    "options": dict|null
                }
            }
            Error (400/404): {
                "status": "error",
                "message": str
            }
    """
    try:
        # Get command
        command = db.session.get(MinecraftCommand, command_id)
        if not command:
            return jsonify({
                'status': 'error',
                'message': 'Command not found'
            }), 404

        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        # Validate command_name
        command_name = data.get('command_name', '').strip()

        if not command_name:
            return jsonify({
                'status': 'error',
                'message': 'Command name is required'
            }), 400

        if len(command_name) > 20:
            return jsonify({
                'status': 'error',
                'message': 'Command name must not exceed 20 characters'
            }), 400

        # Check for duplicate name (excluding current command)
        existing_command = MinecraftCommand.query.filter(
            MinecraftCommand.command_name == command_name,
            MinecraftCommand.command_id != command_id
        ).first()

        if existing_command:
            return jsonify({
                'status': 'error',
                'message': f'Command "{command_name}" already exists'
            }), 400

        # Validate options
        options = data.get('options')
        if options is not None and not isinstance(options, dict):
            return jsonify({
                'status': 'error',
                'message': 'Options must be a JSON object'
            }), 400

        # Capture old name for logging
        old_name = command.command_name

        # Update command
        command.command_name = command_name
        command.options = options
        db.session.commit()

        # Audit logging
        current_app.logger.info(
            f"Command '{old_name}' updated to '{command_name}' by user "
            f"{current_user.id} ({current_user.username})"
        )

        return jsonify({
            'status': 'success',
            'command': {
                'command_id': command.command_id,
                'command_name': command.command_name,
                'options': command.options
            }
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error updating command: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Database error occurred'
        }), 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error updating command: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500


@mc_commands_bp.route('/mc/commands/<int:command_id>/delete', methods=['POST'])
def delete_command(command_id):
    """
    POST - Delete command (form POST with CSRF protection).

    Args:
        command_id: Command ID from URL parameter

    Form data:
        csrf_token: CSRF token (required via DeleteMinecraftCommandForm)

    Returns:
        Redirect to list_commands with flash message
    """
    try:
        command = db.session.get(MinecraftCommand, command_id)
        if not command:
            abort(404)

        form = DeleteMinecraftCommandForm()

        if form.validate_on_submit():
            command_name = command.command_name

            # Delete command
            db.session.delete(command)
            db.session.commit()

            # Audit logging
            current_app.logger.info(
                f"Command '{command_name}' deleted by user "
                f"{current_user.id} ({current_user.username})"
            )

            flash(f'Command "{command_name}" deleted successfully!', 'success')
        else:
            flash('Invalid request.', 'danger')

        return redirect(url_for('mc_commands.list_commands'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Database error occurred while deleting command.', 'danger')
        current_app.logger.error(f"Delete command error: {e}")
        return redirect(url_for('mc_commands.list_commands'))
