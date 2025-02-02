# app/__init__.py
from flask import Blueprint, Flask, g
from flask_celeryext import FlaskCeleryExt
from flask_jwt_extended import JWTManager
from app.EmailConfig.EmailBase import BaseMailer
from app.EmailConfig.EmailService import EmailService
from app.security.security import SecurityHeaders
from .config import Config
from .models import db
from flask_migrate import Migrate
from dotenv import load_dotenv, find_dotenv
from flask_mail import Mail
from flask_socketio import SocketIO     # new
from flask_wtf.csrf import CSRFProtect
from app.extensions import make_celery
import os
from flask_talisman import Talisman
from app.utils.base_logger import BaseLogger
from flask_cors import CORS
from typing import OrderedDict
from flask_caching import Cache



app_logger = BaseLogger(logger_name="AppInitialization").get_logger()

app_logger.info("Initializing Flask application...")


# Initialize Flask extensions
migrate = Migrate()
mail = Mail()
cache = Cache()
socketio = SocketIO()
cors = CORS()
ext_celery = FlaskCeleryExt(create_celery_app=make_celery)
socketio = SocketIO(engineio_logger=True)  
talisman = Talisman()
jwt = JWTManager()


static_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
static_bp = Blueprint('static', __name__, static_folder=static_folder_path)


csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "https://apis.example.com", "https://cdn.example.com"],
    'style-src': ["'self'", "https://fonts.example.com"],
    'img-src': ["'self'", "https://images.example.com", "data:"],  # Allow images from host and inline data URIs
    'connect-src': ["'self'", "http://127.0.0.1:5173"],  # Allow XHR/fetch to a specific host
    'font-src': ["'self'", "http://127.0.0.1"],  # Allow fonts from a specific host
}

load_dotenv(find_dotenv())

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    app.config.from_pyfile('config.py', silent=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Initialize Celery within the factory function
    ext_celery.init_app(app)
    socketio.init_app(app, message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])  
    talisman.init_app(app, content_security_policy=csp)
    cache.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": os.environ.get('ORIGINS')}})
    jwt.init_app(app)

    from app.routes import register_routes
    register_routes(app)
    app.register_blueprint(static_bp, url_prefix='/static')
    # app_logger.info("Application Initialized Successfully...")
    
    
    mailer = BaseMailer(app)
    email_service = EmailService(mailer)
    @app.before_request
    def initialize_services():
        g.email_service = email_service
    SecurityHeaders(app)
    # shell context for flask cli
    
    # print(app.url_map)
    @app.shell_context_processor
    def ctx():
        return {'app': app, 'db': db}
    

    return app


