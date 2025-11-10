from dotenv import load_dotenv
import os

load_dotenv() # load env variables from .env file

class Config:
  # Use SQLite for testing, PostgreSQL for production
  if os.environ.get('TESTING') == 'true':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
  else:
    SQLALCHEMY_DATABASE_URI = f"{os.environ.get('DATABASE_TYPE')}://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}?connect_timeout=10"
    SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_timeout': 10,
            'pool_recycle': 300,
            'pool_pre_ping': True
            }

  LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'WARN')
  RCON_PASS = os.environ.get('RCON_PASS', 'test_password')
  RCON_HOST = os.environ.get('MC_HOST', 'localhost')
  RCON_PORT = os.environ.get('MC_PORT', '25575')
  # Minecraft timeout configuration (seconds)
  MC_QUERY_TIMEOUT = int(os.environ.get('MC_QUERY_TIMEOUT', '5'))
  MC_RCON_TIMEOUT = int(os.environ.get('MC_RCON_TIMEOUT', '10'))
  MC_STATUS_CACHE_DURATION = int(os.environ.get('MC_STATUS_CACHE_DURATION', '10'))
  SECRET_KEY = os.environ.get('SECRET_KEY')
  REGISTRATION_ENABLED = os.environ.get('REGISTRATION_ENABLED', 'True') == 'True'
  BLOG_POST_UPLOAD_FOLDER = os.path.join(os.getcwd(),'uploads/blog-posts')
  PROFILE_UPLOAD_FOLDER = os.path.join(os.getcwd(),'uploads/profiles')
  MAX_CONTENT_LENGTH = 5 * 1024 * 1024 # 5MB limit (security: prevent DoS attacks)
  TIMEZONE = "America/New_York"
  ADMIN_EMAIL = "turingcompletejeff@gmail.com"
  MAIL_SERVER = "smtp.gmail.com"
  MAIL_PORT = 587
  MAIL_USER = os.environ.get('MAIL_USER')
  MAIL_PW = os.environ.get('MAIL_PW')
