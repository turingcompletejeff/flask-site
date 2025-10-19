from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from app.utils.filters import register_filters
import logging

__version__ = "0.2.4" # initial testing fmwk

db = SQLAlchemy()
rcon = None
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure log level
    app.logger.setLevel(app.config.get('LOGGING_LEVEL','WARN'))

    # enable CSRF globally
    csrf.init_app(app)
    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # register timezone filter
    register_filters(app)

    # Ensure upload folders exist
    import os
    os.makedirs(app.config.get('PROFILE_UPLOAD_FOLDER', 'uploads/profiles'), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads/blog-posts'), exist_ok=True)

    # Register blueprints
    from app.routes import (
        main_bp,
        auth_bp,
        blogpost_bp,
        mc_bp,
        admin_bp,
        health_bp,
        profile_bp
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(blogpost_bp)
    app.register_blueprint(mc_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(profile_bp)

    # Exempt health endpoint from CSRF (read-only, no auth required)
    csrf.exempt(health_bp)

    # init global.... RCON object
    app.rcon = rcon

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
