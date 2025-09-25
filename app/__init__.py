import os
from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from .filters import register_filters

db = SQLAlchemy()
rcon = None
#migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Check if we're in testing mode
    if os.environ.get('TESTING') == 'true' or (test_config and test_config.get('TESTING')):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
    else:
        # load normal config
        app.config.from_object(Config)
    
    # enable CSRF globally
    csrf.init_app(app)
    # Initialize Flask extensions
    db.init_app(app)
    #migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # register timezone filter
    register_filters(app)

    # Register blueprints or routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    from app.routes_auth import auth
    app.register_blueprint(auth)
    from app.routes_blogpost import blogpost_bp
    app.register_blueprint(blogpost_bp)
    from app.routes_mc import mc_bp
    app.register_blueprint(mc_bp)
    
    # init global.... RCON object
    app.rcon = rcon

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))
