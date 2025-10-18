from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user
from app import db, rcon
from app.models import MinecraftCommand
from config import Config
from mctools import RCONClient, QUERYClient
import socket

# Create a blueprint for main routes
mc_bp = Blueprint('mc', __name__)

@mc_bp.before_request
def require_login_and_role():
    if not current_user.is_authenticated:
        flash("you must be logged in to access this page.", "warning")
        return redirect(url_for('auth.login'))

    # Check for minecrafter role or admin bypass
    if not current_user.is_admin() and not current_user.has_role('minecrafter'):
        abort(403)  # Forbidden

def rconConnect():
    global rcon
    if rcon is None:
        rcon = RCONClient(Config.RCON_HOST, port=Config.RCON_PORT)
    
    return rcon.login(Config.RCON_PASS)

# Home page
@mc_bp.route('/mc')
def index():
    return render_template('mc.html', current_page="minecraf")

@mc_bp.route('/mc/init')
def rconInit():
    global rcon
    if rconConnect():
        resp = rcon.command("help")
        return resp
    return 'FAIL'

@mc_bp.route('/mc/stop')
def rconStop():
    global rcon
    if rcon is not None:
        rcon.stop()
        rcon = None
    return 'OK'
    
@mc_bp.route('/mc/command', methods = ['POST'])
def rconCommand():
    global rcon
    if rconConnect():
        resp = rcon.command(request.form.get('command'))
        return resp
    return 'FAIL'

@mc_bp.route('/mc/query')
def rconQuery():
    try:
        query = QUERYClient(Config.RCON_HOST)
        return query.get_full_stats()
    except (socket.error, ConnectionResetError) as e:
        return jsonify({"error": "Connection closed", "message": str(e)}), 500

@mc_bp.route('/mc/list')
def list():
    commands = MinecraftCommand.query.order_by(MinecraftCommand.command_id.asc()).all()
    return jsonify([cmd.to_dict() for cmd in commands])
