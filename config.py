from dotenv import load_dotenv
import os

load_dotenv() # load env variables from .env file

class Config:
  SQLALCHEMY_DATABASE_URI = f"{os.environ.get('DATABASE_TYPE')}://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}?connect_timeout=10"
  SQLALCHEMY_ENGINE_OPTIONS = {
          'pool_timeout': 10,
          'pool_recycle': 300,
          'pool_pre_ping': True
          }
  RCON_PASS = os.environ.get('RCON_PASS')
  RCON_HOST = os.environ.get('MC_HOST')
  RCON_PORT = os.environ.get('MC_PORT')
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
