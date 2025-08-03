import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).parent
load_dotenv(basedir / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-is-long-and-random'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Refinery specific config
    REFINERY_PROJECT_PATH = os.path.abspath(
        os.path.join(basedir, '../Refinery/src')
    )

    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
