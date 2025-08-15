from flask import Blueprint, render_template, request, redirect, url_for, flash
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
            flash('Login succesful','success')
            return redirect(url_for('main_bp.index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@auth.route('/register', methods=['GET','POST'])
def register():
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
