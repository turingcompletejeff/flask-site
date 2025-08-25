from dotenv import load_dotenv
import os

load_dotenv() # load env variables from .env file

class Config:
  print({os.environ.get('DB_USERNAME')})
  SQLALCHEMY_DATABASE_URI = f"postgresql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres"
  RCON_PASS = os.environ.get('RCON_PASS')
  RCON_HOST = os.environ.get('MC_HOST')
  RCON_PORT = os.environ.get('MC_PORT')
  SECRET_KEY = os.environ.get('SECRET_KEY')
  REGISTRATION_ENABLED = os.environ.get('REGISTRATION_ENABLED', 'True') == 'True'
  JELLYFIN_API = os.environ.get('JELLYFIN_API_KEY')
  JELLYFIN_URL = "https://turingcomplete.ly/media"
