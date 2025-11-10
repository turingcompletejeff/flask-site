from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import current_user, login_required
from app import db, rcon
from app.models import MinecraftCommand
from config import Config
from mctools import RCONClient, QUERYClient
import socket
from datetime import datetime, timezone
import time

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

# Home page
@mc_bp.route('/mc')
def index():
    return render_template('mc.html', current_page="minecraft")

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
