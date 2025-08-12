from flask import Flask
from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
rcon = None
#migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Flask extensions
    db.init_app(app)
    #migrate.init_app(app, db)

    # Register blueprints or routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    from app.routes_blogpost import blogpost_bp
    app.register_blueprint(blogpost_bp)
    from app.routes_mc import mc_bp
    app.register_blueprint(mc_bp)
    
    # init global.... RCON object
    app.rcon = rcon

    return app