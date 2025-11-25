from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app, send_from_directory
from flask_login import current_user, login_required
from app import db, rcon
from app.models import MinecraftCommand, MinecraftLocation
from app.forms import MinecraftLocationForm
from app.utils.file_validation import validate_image_file, sanitize_filename
from app.utils.image_utils import delete_uploaded_images
from config import Config
from mctools import RCONClient, QUERYClient
from werkzeug.utils import secure_filename
from PIL import Image
import socket
from datetime import datetime, timezone
import time
import os

# Create a blueprint for main routes
mc_bp = Blueprint('mc', __name__)

# Status cache for /mc/status endpoint
_status_cache = None
_status_cache_time = None

@mc_bp.before_request
def require_login_and_role():
    if not current_user.is_authenticated:
        flash("you must be logged in to access this page.", "warning")
        return redirect(url_for('auth.login'))

    # Check for minecrafter role or admin bypass
    if not current_user.is_admin() and not current_user.has_role('minecrafter'):
        abort(403)  # Forbidden

def rconConnect():
    """
    Establish RCON connection to Minecraft server.
    Returns RCONClient on success, None on failure.
    """
    global rcon
    host = Config.RCON_HOST
    port = Config.RCON_PORT
    password = Config.RCON_PASS
    timeout = Config.MC_RCON_TIMEOUT

    try:
        if rcon is None:
            rcon = RCONClient(host, port=int(port))

        if rcon.login(password):
            current_app.logger.info(f"RCON connected: {host}:{port}")
            return rcon
        else:
            current_app.logger.warning(f"RCON authentication failed: {host}:{port}")
            return None

    except socket.timeout:
        current_app.logger.warning(f"RCON connection timeout ({timeout}s): {host}:{port}")
        return None

    except ConnectionRefusedError:
        current_app.logger.warning(f"RCON connection refused: {host}:{port}")
        return None

    except (ConnectionResetError, socket.error) as e:
        current_app.logger.warning(f"RCON connection error: {e}")
        return None

    except Exception as e:
        current_app.logger.error(f"RCON connection unexpected error: {e}", exc_info=True)
        return None

@mc_bp.route('/uploads/minecraft-locations/')
def uploaded_files_dir():
    return send_from_directory(current_app.config['MC_LOCATION_UPLOAD_FOLDER'])

@mc_bp.route('/uploads/minecraft-locations/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['MC_LOCATION_UPLOAD_FOLDER'], filename)

# Home page
@mc_bp.route('/mc')
def index():
    form = MinecraftLocationForm()
    return render_template('mc.html', current_page="minecraft", form=form)

@mc_bp.route('/mc/init')
def rconInit():
    global rcon
    if rconConnect():
        resp = rcon.command("help")
        return resp
    return 'FAIL'

@mc_bp.route('/mc/stop')
def rconStop():
    """
    Stop RCON connection to Minecraft server.
    Handles disconnection errors gracefully.
    """
    global rcon

    if rcon:
        try:
            rcon.stop()
            current_app.logger.info("RCON connection closed")
        except (socket.error, OSError) as e:
            current_app.logger.warning(f"RCON disconnect error (ignoring): {e}")
        except Exception as e:
            current_app.logger.error(f"RCON stop unexpected error: {e}", exc_info=True)
        finally:
            rcon = None  # Always clear connection

    return 'OK'
    
@mc_bp.route('/mc/command', methods = ['POST'])
def rconCommand():
    """
    Execute RCON command on Minecraft server.
    Returns JSON response with command output or error.
    """
    global rcon
    command = request.form.get('command')

    if not command:
        return jsonify({
            'status': 'error',
            'message': 'No command provided'
        }), 400

    if not rconConnect():
        return jsonify({
            'status': 'error',
            'message': 'RCON not connected'
        }), 200

    try:
        resp = rcon.command(command)
        current_app.logger.info(f"RCON command executed: {command}")
        return resp

    except socket.timeout:
        current_app.logger.warning(f"RCON command timeout: {command}")
        return jsonify({
            'status': 'error',
            'message': 'Command timeout (server not responding)'
        }), 200

    except (ConnectionResetError, socket.error) as e:
        rcon = None  # Clear broken connection
        current_app.logger.warning(f"RCON command connection lost: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Connection lost (server shutdown?)'
        }), 200

    except Exception as e:
        current_app.logger.error(f"RCON command error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Command execution failed'
        }), 200

@mc_bp.route('/mc/query')
def rconQuery():
    """
    Query Minecraft server for full statistics.
    Returns JSON with server info or error message.
    """
    host = Config.RCON_HOST
    timeout = Config.MC_QUERY_TIMEOUT

    try:
        query = QUERYClient(host)
        stats = query.get_full_stats()
        current_app.logger.info(f"MC query succeeded: {host}")

        return jsonify({
            'status': 'success',
            'data': stats
        }), 200

    except socket.timeout:
        current_app.logger.warning(f"MC query timeout ({timeout}s): {host}")
        return jsonify({
            'status': 'error',
            'message': f'Server not responding (timeout after {timeout}s)'
        }), 200

    except ConnectionRefusedError:
        current_app.logger.warning(f"MC query connection refused: {host}")
        return jsonify({
            'status': 'error',
            'message': 'Server offline or port closed'
        }), 200

    except (ConnectionResetError, socket.error) as e:
        current_app.logger.warning(f"MC query connection error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Connection lost or network error'
        }), 200

    except OSError as e:
        current_app.logger.error(f"MC query OS error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'System error accessing server'
        }), 200

    except Exception as e:
        current_app.logger.error(f"MC query unexpected error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Query failed'
        }), 200

@mc_bp.route('/mc/list')
def list():
    commands = MinecraftCommand.query.order_by(MinecraftCommand.command_id.asc()).all()
    return jsonify([cmd.to_dict() for cmd in commands])

def _fetch_server_status():
    """
    Internal helper to fetch fresh server status.
    Returns dict with status information.
    """
    host = Config.RCON_HOST
    timeout = Config.MC_QUERY_TIMEOUT
    start_time = time.time()

    # Quick TCP connection test first (faster offline detection)
    # Test if Minecraft server port is open before attempting full query
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(2)  # 2 second timeout for quick test
        test_socket.connect((host, 25565))  # Minecraft server port (TCP)
        test_socket.close()
        current_app.logger.debug(f"MC status: TCP connection test passed")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        # Quick test failed - server is offline
        current_app.logger.info(f"MC status: TCP connection test failed - server offline ({e})")
        return {
            'status': 'offline',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server_address': host,
            'query_time_ms': int((time.time() - start_time) * 1000),
            'error': 'Server offline or unreachable'
        }

    # TCP test passed - proceed with full query
    try:
        query = QUERYClient(host)
        stats = query.get_full_stats()
        query_time_ms = int((time.time() - start_time) * 1000)

        # Extract relevant fields from full stats
        # Convert numplayers and maxplayers to integers (mctools may return strings)
        numplayers = int(stats.get('numplayers', 0)) if stats.get('numplayers') else 0
        maxplayers = int(stats.get('maxplayers', 0)) if stats.get('maxplayers') else 0

        status_data = {
            'status': 'online',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server_address': host,
            'query_time_ms': query_time_ms,
            'players': {
                'online': numplayers,
                'max': maxplayers,
                'list': stats.get('players', []) if stats.get('players') else []
            },
            'version': stats.get('version', 'Unknown'),
            'motd': stats.get('motd', ''),
            'map': stats.get('map', 'Unknown'),
            'plugins': stats.get('plugins', '')
        }

        current_app.logger.info(f"MC status: online ({query_time_ms}ms)")
        return status_data

    except socket.timeout:
        current_app.logger.warning(f"MC status timeout ({timeout}s): {host}")
        return {
            'status': 'offline',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server_address': host,
            'query_time_ms': int((time.time() - start_time) * 1000),
            'error': f'Connection timeout after {timeout} seconds'
        }

    except ConnectionRefusedError:
        current_app.logger.warning(f"MC status connection refused: {host}")
        return {
            'status': 'offline',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server_address': host,
            'query_time_ms': int((time.time() - start_time) * 1000),
            'error': 'Server offline or port closed'
        }

    except (ConnectionResetError, socket.error) as e:
        current_app.logger.warning(f"MC status connection error: {e}")
        return {
            'status': 'offline',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server_address': host,
            'query_time_ms': int((time.time() - start_time) * 1000),
            'error': 'Connection lost or network error'
        }

    except Exception as e:
        # Treat most errors as offline - if we can't query it, it's effectively offline
        current_app.logger.warning(f"MC status error (treating as offline): {e}")
        return {
            'status': 'offline',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server_address': host,
            'query_time_ms': int((time.time() - start_time) * 1000),
            'error': f'Unable to connect: {str(e)}'
        }

@mc_bp.route('/mc/status')
def mc_status():
    """
    Get cached Minecraft server status.
    Returns JSON with status, timestamp, and optional player info.
    Caches results for MC_STATUS_CACHE_DURATION seconds.
    """
    global _status_cache, _status_cache_time

    cache_duration = Config.MC_STATUS_CACHE_DURATION
    now = time.time()

    # Check cache validity
    if _status_cache_time and (now - _status_cache_time) < cache_duration:
        current_app.logger.debug("MC status: returning cached result")
        return jsonify(_status_cache), 200

    # Fetch fresh status
    status_data = _fetch_server_status()

    # Update cache
    _status_cache = status_data
    _status_cache_time = now

    return jsonify(status_data), 200


# ============================================================================
# Minecraft Fast Travel Location Routes (TC-46)
# ============================================================================

@mc_bp.route('/mc/locations', methods=['GET'])
def list_locations():
    """
    Get all fast travel locations.
    Returns JSON array of locations ordered by name.

    Response:
        JSON array of location objects with:
        - id: Location ID
        - name: Location name
        - description: Location description
        - position: {x, y, z} coordinates
        - portrait: Portrait image filename
        - thumbnail: Thumbnail image filename
        - created_at: ISO 8601 timestamp
        - created_by_id: Creator user ID
    """
    locations = MinecraftLocation.query.order_by(MinecraftLocation.name.asc()).all()
    return jsonify([loc.to_dict() for loc in locations]), 200


@mc_bp.route('/mc/locations/<int:location_id>', methods=['GET'])
def get_location(location_id):
    """
    Get a single location by ID.

    Args:
        location_id: Location ID

    Returns:
        JSON object with full location data

    Raises:
        404: Location not found
    """
    location = db.session.get(MinecraftLocation, location_id)
    if not location:
        abort(404)

    return jsonify(location.to_dict()), 200


@mc_bp.route('/mc/locations/create', methods=['POST'])
@login_required
def create_location_ajax():
    """
    Create a new fast travel location via AJAX form submission.

    POST: Process form submission, validate, and save location
    Returns: JSON response with success/error status

    Authorization:
        Requires 'minecrafter' or 'admin' role (enforced by before_request)

    Form Data:
        - name: Location name (required)
        - description: Location description (optional)
        - position_x: X coordinate (required, float)
        - position_y: Y coordinate (required, float)
        - position_z: Z coordinate (required, float)
        - portrait: Portrait image file (optional)
        - thumbnail: Custom thumbnail (optional)

    Returns:
        201: Location created successfully
        400: Validation errors
    """
    form = MinecraftLocationForm()

    if form.validate_on_submit():
        # Process portrait and thumbnail images
        portrait_file = form.portrait.data
        thumbnail_file = form.thumbnail.data
        filename = None
        thumbnailname = None

        # Validate and save portrait
        if portrait_file:
            is_valid, error_msg = validate_image_file(portrait_file)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'errors': {'portrait': [f'Portrait upload failed: {error_msg}']}
                }), 400

            safe_filename_str = sanitize_filename(portrait_file.filename)
            filename = secure_filename(safe_filename_str)
            file_path = os.path.join(current_app.config['MC_LOCATION_UPLOAD_FOLDER'], filename)

            try:
                portrait_file.save(file_path)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'errors': {'portrait': [f'Error saving portrait: {str(e)}']}
                }), 400

        # Handle thumbnail (custom or auto-generated from portrait)
        if thumbnail_file:
            is_valid, error_msg = validate_image_file(thumbnail_file)
            if not is_valid:
                # Cleanup portrait if saved
                if portrait_file and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                return jsonify({
                    'success': False,
                    'errors': {'thumbnail': [f'Thumbnail upload failed: {error_msg}']}
                }), 400

            safe_thumb_name = sanitize_filename(thumbnail_file.filename)
            thumbnailname = f"custom_thumb_{secure_filename(safe_thumb_name)}"
            thumb_path = os.path.join(current_app.config['MC_LOCATION_UPLOAD_FOLDER'], thumbnailname)

            try:
                thumbnail_file.save(thumb_path)
                img = Image.open(thumb_path)
                img.thumbnail((300, 300))
                img.save(thumb_path)
            except Exception as e:
                # Cleanup portrait if saved
                if portrait_file and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                return jsonify({
                    'success': False,
                    'errors': {'thumbnail': [f'Error processing thumbnail: {str(e)}']}
                }), 400

        elif portrait_file:
            # Auto-generate thumbnail from portrait
            thumbnailname = f"thumb_{filename}"
            thumb_path = os.path.join(current_app.config['MC_LOCATION_UPLOAD_FOLDER'], thumbnailname)
            try:
                img = Image.open(file_path)
                img.thumbnail((300, 300))
                img.save(thumb_path)
            except Exception as e:
                # Cleanup portrait
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                return jsonify({
                    'success': False,
                    'errors': {'portrait': [f'Error generating thumbnail: {str(e)}']}
                }), 400

        # Create location record
        location = MinecraftLocation(
            name=form.name.data,
            description=form.description.data,
            position_x=form.position_x.data,
            position_y=form.position_y.data,
            position_z=form.position_z.data,
            portrait=filename,
            thumbnail=thumbnailname,
            created_by_id=current_user.id
        )

        db.session.add(location)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Location "{location.name}" created!',
            'location': location.to_dict()
        }), 201

    # Form validation failed
    errors = {}
    for field_name, error_list in form.errors.items():
        errors[field_name] = error_list

    return jsonify({
        'success': False,
        'errors': errors
    }), 400


@mc_bp.route('/mc/locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_location(location_id):
    """
    Edit an existing fast travel location.

    GET: Return form pre-populated with location data (JSON)
    POST: Update location with form data

    Args:
        location_id: Location ID to edit

    Authorization:
        Creator or admin can edit (enforced by before_request for role)

    Returns:
        GET: 200 with location data
        POST: 200 on success, 400 on validation error
        403: Not authorized (not creator or admin)
        404: Location not found
    """
    location = db.session.get(MinecraftLocation, location_id)
    if not location:
        abort(404)

    # Authorization check: only creator or admin can edit
    if not current_user.is_admin() and location.created_by_id != current_user.id:
        abort(403)

    form = MinecraftLocationForm()

    if request.method == 'GET':
        # Pre-populate form with location data
        form.name.data = location.name
        form.description.data = location.description
        form.position_x.data = location.position_x
        form.position_y.data = location.position_y
        form.position_z.data = location.position_z
        return render_template('edit_location.html', form=form, location=location)

    if form.validate_on_submit():
        # Update basic fields
        location.name = form.name.data
        location.description = form.description.data
        location.position_x = form.position_x.data
        location.position_y = form.position_y.data
        location.position_z = form.position_z.data

        # Handle portrait replacement
        portrait_file = form.portrait.data
        if portrait_file:
            # Validate new portrait
            is_valid, error_msg = validate_image_file(portrait_file)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'errors': {'portrait': [f'Portrait upload failed: {error_msg}']}
                }), 400

            # Store old images for cleanup
            old_portrait = location.portrait
            old_thumbnail = location.thumbnail

            # Save new portrait
            safe_filename_str = sanitize_filename(portrait_file.filename)
            filename = secure_filename(safe_filename_str)
            file_path = os.path.join(current_app.config['MC_LOCATION_UPLOAD_FOLDER'], filename)

            try:
                portrait_file.save(file_path)
                location.portrait = filename

                # Auto-generate thumbnail
                thumbnailname = f"thumb_{filename}"
                thumb_path = os.path.join(current_app.config['MC_LOCATION_UPLOAD_FOLDER'], thumbnailname)
                img = Image.open(file_path)
                img.thumbnail((300, 300))
                img.save(thumb_path)
                location.thumbnail = thumbnailname

                # Clean up old files
                delete_uploaded_images(
                    current_app.config['MC_LOCATION_UPLOAD_FOLDER'],
                    [old_portrait, old_thumbnail]
                )
            except Exception as e:
                return jsonify({
                    'success': False,
                    'errors': {'portrait': [f'Error updating images: {str(e)}']}
                }), 400

        db.session.commit()
        flash(f'Location "{location.name}" updated!', 'success')
        return redirect(url_for('mc.index'))

    # Form validation failed - render template with errors
    return render_template('edit_location.html', form=form, location=location)


@mc_bp.route('/mc/locations/<int:location_id>/delete', methods=['POST'])
@login_required
def delete_location(location_id):
    """
    Delete a fast travel location.
    Returns JSON response for AJAX requests.

    Args:
        location_id: Location ID to delete

    Authorization:
        Creator or admin can delete (enforced by before_request for role)

    Returns:
        200: Location deleted successfully
        403: Not authorized (not creator or admin)
        404: Location not found
    """
    location = db.session.get(MinecraftLocation, location_id)
    if not location:
        abort(404)

    # Authorization check: only creator or admin can delete
    if not current_user.is_admin() and location.created_by_id != current_user.id:
        abort(403)

    # Store images before deletion
    portrait = location.portrait
    thumbnail = location.thumbnail
    location_name = location.name

    # Delete from database
    db.session.delete(location)
    db.session.commit()

    # Clean up image files
    result = delete_uploaded_images(
        current_app.config['MC_LOCATION_UPLOAD_FOLDER'],
        [portrait, thumbnail]
    )

    # Build JSON response
    if result['errors']:
        message = f'Location deleted, but {len(result["errors"])} image(s) could not be removed.'
        return jsonify({
            'success': True,
            'message': message,
            'warnings': result['errors']
        }), 200
    else:
        return jsonify({
            'success': True,
            'message': f'Location "{location_name}" deleted!'
        }), 200
