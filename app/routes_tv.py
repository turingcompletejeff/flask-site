from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required

tv = Blueprint('tv',__name__)

@tv.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard")

@tv.route("/list")
@login_required
def list():
    

@tv.route("/play/<item_id>")
@login_required
def play_item(item_id):
    user = current_user
    hls_url = f"{JELLYFIN_URL}/Videos/{item_id}/master.m3u8?api_key={user.jellyfin_session_token}"
    return render_template("player.html", hls_url=hls_url)

