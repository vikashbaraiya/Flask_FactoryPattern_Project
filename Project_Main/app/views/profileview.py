

import os
from flask import jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity
from app.models import User
from app.services.baseservice import BaseService
from app.services.userservice import UserService
from app.utils.base_logger import BaseLogger
from app.utils.helpers import UtilityHelper
from werkzeug.utils import secure_filename
from app.config import Config


if not os.path.exists(Config.BASE_UPLOAD_FOLDER):
    os.makedirs(Config.BASE_UPLOAD_FOLDER)


app_logger = BaseLogger(logger_name="ProfileView").get_logger()

def update_user_profile_image():
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and UtilityHelper.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        fl_name = filename.split('.')
        username = request.form.get('user_name')
        user_id = request.form.get('user_id')  # For example, get user ID from form or token
        file_name = username+'_'+str(user_id)+'.'+fl_name[1]
        file_path = os.path.join(Config.UPLOAD_FOLDER, file_name)
        UtilityHelper.delete_old_file(file_path)
        file.save(file_path)
        
        # Get the current user (assuming authentication is done via session or token)
        user_image = User.query.get(user_id)
        
        if user_image is None:
            return jsonify({"error": "User not found"}), 404
        
        if user_image is None:
            UserService.update_user(user_id, file_name=file_path)
        else:
            user_image.file_name =file_path
            BaseService._commit_session()

        file_path = url_for('static', filename=f"images/{file_path.split('/')[-1]}", _external=True)
        return jsonify({"message": "Profile updated successfully", "image_url": file_path}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400
    


def update_user_profile(data):
    user_id = get_jwt_identity()  # Fetch current user ID from JWT
    user = UserService.get_user_by_id(user_id)
    # Check if user exists
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Validate required fields
    if not data.get("first_name"):
        return jsonify({"error": "First name field cannot be empty"}), 400
    if not data.get("last_name"):
        return jsonify({"error": "Last name field cannot be empty"}), 400

    # Update user details
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)

    # Update password if provided
    if 'password' in data and data.get("password"):
        user.set_password(data['password'])  # Ensure this method hashes the password

    try:
        # Commit changes to the database
        if BaseService._commit_session():
            return jsonify({
                "message": "Profile updated successfully",
                "user": user.serialize()  # Serialize user data
            }), 200
        else:
            return jsonify({"error": "Failed to update profile"}), 500
    except Exception as e:
        # Log the exception (replace print with logger in production)
        print(f"Exception occurred: {e}")
        return jsonify({"error": str(e)}), 500
    

def get_profile_data():
    # Get the current user from JWT token
    user_id = get_jwt_identity()  
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Return the serialized user data
    return jsonify({
        "message": "User profile retrieved successfully",
        "user": user.serialize()
    }), 200