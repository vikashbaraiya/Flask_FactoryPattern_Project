from .auth import auth_bp
from .profile import profile_bp
from .account import account_bp
from .exchange import exchange_bp
from .bot import bot_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(exchange_bp)
    app.register_blueprint(bot_bp)