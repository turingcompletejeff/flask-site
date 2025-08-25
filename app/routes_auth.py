from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
import uuid
from app import db
from app.models import User
from config import Config
import logging
import requests

auth = Blueprint('auth',__name__)
logger = logging.getLogger(__name__)

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"welcome, {user.username}",'success')

            # if u.roles is ADMIN or CONTAINS TV:
            if not user.jellyfin_device_id:
                logger.info('no SSO user attached, generating one...')
                if create_jellyfin_user(user):
                    logger.info('jellyfin SSO user created!')
                else:
                    logger.error('error creating jellyfin user')
                    return redirect(url_for('main_bp.index'))

            logger.info('grabbing new jellyfin token')
            token = get_jellyfin_session_token(user)
            if token:
                user.jellyfin_session_token = token
                logger.info('committing to db')
                db.session.commit()
            else:
                logger.warning('jellyfin failed to auth')

            return redirect(url_for('main_bp.index'))
        else:
            flash('invalid username or password', 'danger')

    return render_template('login.html', registration_enabled=current_app.config['REGISTRATION_ENABLED'])

@auth.route('/register', methods=['GET','POST'])
def register():
    if not current_app.config.get('REGISTRATION_ENABLED', True):
        flash("registration is temporarily disabled.","warning")
        return redirect(url_for('main_bp.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if User.query.filter_by(username=username).first():
            flash('Username taken','danger')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created!','success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("logged out", "info")
    return redirect(url_for('main_bp.index'))



def create_jellyfin_user(flask_user):
    if not flask_user.jellyfin_device_id:
        flask_user.jellyfin_device_id = str(uuid.uuid4())

    url = f"{Config.JELLYFIN_URL}/Users/New"
    headers = {"X-Emby-Token": Config.JELLYFIN_API}
    data = {
            "Name": flask_user.username,
            "Password": ""
    }
    r = requests.post(url, json=data, headers=headers)

    if r.status_code == 200:
        user_data = r.json()
        flask_user.jellyfin_user_id = user_data["Id"]
        db.session.commit()
        return True
    return False

def get_jellyfin_session_token(user):
    """
    Authenticates the user with jellyfin and returns the session token.
    """
    url = f"{Config.JELLYFIN_URL}/Users/AuthenticateByName"
    headers = {
            "X-Emby-Authorization": (
                f'MediaBrowser Client="FlaskMediaPortal", '
                f'Device="FlaskWeb", '
                f'DeviceId="{user.jellyfin_device_id}", '
                f'Version="1.0.0"'
            )
        }
    data = {"Username": user.username, "Pw": ""}
    r = requests.post(url, json=data, headers=headers)

    if r.status_code == 200:
        return r.json()["AccessToken"]
    return None
