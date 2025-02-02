from functools import wraps
from flask import jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, unset_jwt_cookies
from app.models import User


def get_current_user():
    # Get the identity from the JWT token
    user_id = get_jwt_identity()

    # Fetch the user from the database
    return User.query.get(user_id) if user_id else None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Retrieve the current user using your auth mechanism
        current_user = get_current_user()  

        # Check if the user has the 'Admin' role
        if not current_user or not current_user.has_role('admin'):
            return jsonify({'message': 'Access denied, Admin role required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function