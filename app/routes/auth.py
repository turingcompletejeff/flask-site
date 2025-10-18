from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import User

auth = Blueprint('auth',__name__)

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"welcome, {user.username}",'success')
            return redirect(url_for('main.index'))
        else:
            flash('invalid username or password', 'danger')

    return render_template('login.html', registration_enabled=current_app.config['REGISTRATION_ENABLED'])

@auth.route('/register', methods=['GET','POST'])
def register():
    if not current_app.config.get('REGISTRATION_ENABLED', True):
        flash("registration is temporarily disabled.","warning")
        return redirect(url_for('main.index'))

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
    return redirect(url_for('main.index'))
