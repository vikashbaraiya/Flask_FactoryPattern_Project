from datetime import timedelta
import os
from app.tasks.bot_tasks import add_bot_logs

class Config:

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    PRIVATE_KEY_PATH = os.path.join(BASE_DIR, 'certificate', 'private_key.pem')
    PUBLIC_KEY_PATH = os.path.join(BASE_DIR, 'certificate', 'public_key.pem')

    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use environment variable in production

    # Session and Cache configuration
    SESSION_TYPE = 'filesystem'  # Store sessions on the server
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    # SSL configuration for requests (if applicable)
    SSL_REQUEST_CSR = os.path.join(os.getcwd(), "certificate/request.csr")
    SSL_KEY_FILE = os.path.join(os.getcwd(), "certificate/keyfile.key")

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')  # Default SQLite DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'bjhdjfdf890remefc9e58u405cq4mi4-545mc094m5c9p45m495')
    JWT_TOKEN_LOCATION = ['headers']
    JWT_ALGORITHM = 'RS256'  # Using RSA256 for asymmetric signing
    JWT_PRIVATE_KEY = open(PRIVATE_KEY_PATH, 'r').read()
    JWT_PUBLIC_KEY = open(PUBLIC_KEY_PATH, 'r').read()
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=10)  # Set token expiration time to 10 hours
    
    # File upload settings
    UPLOAD_FOLDER = 'static/images'
    BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), UPLOAD_FOLDER)

    # Email settings for sending email
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Flask-Mail configuration (for email)
    MAIL_USE_SSL = False  # If SSL is required, you can set this to True
    MAIL_DEBUG = False  # Set to False in production

    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    SOCKETIO_MESSAGE_QUEUE = os.environ.get(
        'SOCKETIO_MESSAGE_QUEUE',
        'redis://127.0.0.1:6379/0'
    )
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_BEAT_SCHEDULE = {}  # We'll define the schedule dynamically using the Django-Celery-Beat database
    
    CELERY_BEAT_SCHEDULE = {
    'add-bot-logs-every-30-seconds': {
        'task': 'app.tasks.bot_tasks.add_bot_logs',
        'schedule': 30.0,  # Every 30 seconds
        },
    'store-account-state-every-minute': {
        'task': 'app.tasks.bot_tasks.store_account_state_periodically',
        'schedule': 60.0,  # Every 60 seconds (1 minute)
        },
    }
    CELERY_ACCEPT_CONTENT = ['application/json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    # Enable debug mode (only for development)
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
