import os
from sqlite3 import IntegrityError
from flask import json, jsonify, make_response, request, session
from datetime import datetime, timedelta

from flask_jwt_extended import get_jwt_identity
from app.models import *
from app.utils.helpers import UtilityHelper
from app.utils.validator import DataValidator
from app.EmailConfig.EmailService import EmailService
from app.EmailConfig.EmailBase import BaseMailer
from app.services.baseservice import BaseService
from app.utils.base_logger import BaseLogger
from app import create_app
from app.utils.config_loader import conf_bot_url, auth_user_type
from flask import g
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, unset_jwt_cookies
from flask_wtf.csrf import CSRFProtect, generate_csrf


app_logger = BaseLogger(logger_name="AppInitialization").get_logger()



def signup(data):
    email = data.get('email')
    if not email:
        return jsonify({'message': 'Email is required.'}), 400

    # Check if the user already exists
    if User.query.filter_by(email=email).first():
        app_logger.info(f"Username with this email {email} already exists.")
        return jsonify({'message': 'User already exists.'}), 400

    # Verify the role exists
    user_role = Role.query.filter_by(name=auth_user_type).first()
    if not user_role:
        return jsonify({'message': 'User role does not exist. Please create it first.'}), 500

    # Validate email
    is_valid, message = DataValidator.validate_email(email)
    if not is_valid:
        return jsonify({'message': message}), 400

    # Password validation
    if not DataValidator.validate_password(data.get('password')):
        return jsonify({'message': 'Password does not meet complexity requirements.'}), 400

    # Create a new user
    new_user = User(
        email=email,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        otp=str(UtilityHelper.random_number()),
        otp_generated_at=datetime.now()
    )
    new_user.set_password(data['password'])
    new_user.roles.append(user_role)
    BaseService._add_instance(new_user)
    # Create a default account for the user
    timestamp = int(datetime.now().timestamp())
    default_account_name = f"{data.get('first_name', 'user')}_{timestamp}"
    user = User.query.filter_by(email=email).first()
    account = Account(name=default_account_name, user_id=user.id, default=True)
    BaseService._add_instance(account)

    # Commit the user and account to the database
    

    # Send OTP email
    try:
        email_service = g.email_service
        email_service.send_otp_email(new_user.first_name, new_user.otp, new_user.email)
    except Exception as email_error:
        app_logger.error(f"Failed to send email to {email}: {str(email_error)}")
        return jsonify({'message': 'Failed to send OTP email. Please try again later.'}), 500

    try:
        BaseService._commit_session()
    except IntegrityError:
        db.session.rollback()
        app_logger.error(f"IntegrityError: Duplicate entry for {email}")
        return jsonify({'message': 'A conflict occurred while processing your request.'}), 400

    return jsonify({'message': 'Signup successful. Please check your email to verify your OTP.'}), 201

def add_role(data):
    """
    Handles the logic for adding a new role.
    """
    try:
        # Clean and sanitize input data
        data = UtilityHelper.clean_bleach(data)

        # Ensure the 'name' field is present
        if not data or 'name' not in data:
            return jsonify({'message': 'Role name is required'}), 400

        # Check if the role already exists
        role_name = data['name']
        existing_role = Role.query.filter_by(name=role_name).first()
        if existing_role:
            return jsonify({'message': 'Role already exists'}), 400

        # Create a new role
        new_role = Role(name=role_name)
        saved_role = BaseService.save_instance(new_role)
        if saved_role:
            return jsonify({'message': f'Role {role_name} added successfully'}), 201
        else:
            return jsonify({'message': 'Failed to save role'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    

def get_user_data():
    """
    Retrieves the current user information using the JWT identity.
    """
    try:
        # Extract the user ID from the JWT
        current_user_id = get_jwt_identity()

        # Log the user ID for debugging
        app_logger.debug(f"Token verified for user ID: {current_user_id}")

        # Retrieve user information from the database
        user = User.query.get(current_user_id)
        if user:
            user_data = user.serialize()  # Assuming User model has a serialize method
            return jsonify({
                'message': 'Token is valid',
                'data': user_data,
                'user_id': current_user_id
            }), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    except Exception as e:
        app_logger.error(f"Error retrieving user: {str(e)}")
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500
    

def get_users_data():
    """
    Retrieves all users from the database.
    """
    try:
        # Query all users from the database
        users_list = User.query.all()
        users = [
            {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
            for user in users_list
        ]
        return jsonify(users), 200
    except Exception as e:
        app_logger.error(f"Error retrieving users: {str(e)}")
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500
    

def verify_otp(data):
    """
    Verifies the OTP for a user.
    """
    email = data.get('email')
    otp = data.get('otp')

    # Validate input
    if not email or not otp:
        return jsonify({'message': 'Email and OTP are required.'}), 400

    # Find user by email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'No user found with this email.'}), 404

    if user.confirmed:
        return jsonify({'message': 'Email is already confirmed.'}), 400

    # Check if OTP is valid
    if user.otp == otp:
        if datetime.now() - user.otp_generated_at <= timedelta(minutes=5):
            # Mark user as confirmed and clear OTP
            user.confirmed = True
            user.otp = None
            user.otp_generated_at = None
            BaseService._commit_session()

            # Send welcome email via email service
            try:
                email_service = g.email_service  # Access email service from g
                email_service.send_welcome_email(user.first_name, user.email)

                app_logger.info(f'Email {email} is confirmed')
                return jsonify({'message': 'Email verified and welcome email sent'}), 200
            except Exception as email_error:
                app_logger.error(f"Failed to send welcome email: {str(email_error)}")
                return jsonify({'message': 'Email verification succeeded, but failed to send welcome email.'}), 500
        else:
            app_logger.info("OTP has expired. Please request a new one.")
            return jsonify({'message': 'OTP has expired. Please request a new one.'}), 400
    else:
        app_logger.info("Invalid OTP. Please try again.")
        return jsonify({'message': 'Invalid OTP. Please try again.'}), 400
    

def resend_otp(data):
    
    email = data['email']

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'No user found with this email.'}), 404

    if user.confirmed:
        return jsonify({'message': 'Email is already confirmed.'}), 400

    # Check if OTP exists and if it is still valid
    if user.otp is not None:
        if datetime.now() - user.otp_generated_at < timedelta(minutes=1):
            return jsonify({"message": "Please wait until the previous OTP expires before requesting a new one."}), 400
        else:
            # Clear the expired OTP
            user.otp = None
            user.otp_generated_at = None
            BaseService._commit_session()

    # Generate a new 6-digit OTP
    user.otp = str(UtilityHelper.random_number())
    user.otp_generated_at = datetime.now()  # Reset the timestamp
    db.session.commit()
    email_service = g.email_service
    email_service.send_resend_otp_email(user.first_name, user.otp, user.email)
    

    app_logger.info(f"New OTP email resent to {email}.")
    return jsonify({'message': 'New OTP has been resent. Please check your inbox.'}), 200


def signin(data):
    
    email = data['email']
    password = data['password']

    app_logger.debug(f"Attempting sign-in for email: {email}")

    # Query user from database
    user = User.query.filter_by(email=email).first()

    # Check if user exists and verify password
    if user:
        if user.confirmed:  # Check if the user has confirmed their email
            if user.check_password(password):
                access_token = create_access_token(identity=user.id)
                app_logger.debug(f"Sign-in successful for user: {user.email}")
                # Store user id in session
                session.user_id = user.id
                user_data = user.serialize()
                csrf_token = generate_csrf()
                response = make_response(jsonify({'message': 'Logged in successful', "data": user_data,'csrf_token': csrf_token, 'access_token': access_token}))
                response.set_cookie('csrf_token', csrf_token,  httponly=True, secure=True, samesite='None')
                return response
            app_logger.debug(f"Invalid password for email: {email}")
            return jsonify({'message': 'Invalid password'}), 401
        else:
            app_logger.debug(f"User email not confirmed for email: {email}")
            return jsonify({'message': 'OTP sent. Verify your email to continue.'}), 403

    app_logger.debug(f"Invalid sign-in attempt for email: {email}")
    return jsonify({'message': 'Invalid email or user not found'}), 401


def logout_user():
    # Clear session data
    session.clear()
    app_logger.debug(f"Logout Successfully !!")
    # Clear JWT cookies
    resp = jsonify({'message': 'Logged out successfully'}),200
    unset_jwt_cookies(resp)
    return resp


def forgot_password(data):
    email = data['email']
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'No user found with this email.'}), 404

    # Generate and send OTP
    otp = str(UtilityHelper.random_number())  # Generate a 6-digit OTP
    user.otp = otp  # Assuming the User model has an otp field
    user.otp_generated_at = datetime.now()
    db.session.commit()  # Save the OTP to the database
     # Prepare OTP email template
    email_service = g.email_service
    email_service.send_forgot_password_otp(user.first_name, user.otp, email)

    app_logger.info(f"Password reset OTP sent to {email}.")
    return jsonify({'message': 'OTP sent to your email. Please check your inbox.'}), 200



def verify_forgot_password_otp(data):
    email = data['email']
    otp = data['otp']
    user = User.query.filter_by(email=email).first()
    if not user or user.otp != otp:
        return jsonify({'message': 'Invalid OTP.'}), 400
    if datetime.now() - user.otp_generated_at <= timedelta(minutes=5):
        # Clear the OTP after verification
        user.otp = None
        user.otp_generated_at = None
        db.session.commit()
        return jsonify({'message': 'OTP verified successfully! You can now reset your password.'}), 200
    else:
        return jsonify({"message":"OTP has expired. Please request a new one."})
    


def resend_reset_otp(data):
    email = data['email']
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'No user found with this email.'}), 404

    # Check if OTP exists and if it is still valid
    if user.otp is not None:
        if datetime.now() - user.otp_generated_at < timedelta(minutes=1):
            return jsonify({"message": "Please wait until the previous OTP expires before requesting a new one."}), 400
        else:
            # Clear the expired OTP
            user.otp = None
            user.otp_generated_at = None
            db.session.commit()

    # Generate a new 6-digit OTP
    user.otp = str(UtilityHelper.random_number())
    user.otp_generated_at = datetime.now()  # Reset the timestamp
    db.session.commit()

    email_service = g.email_service
    email_service.send_resend_otp_email(user.first_name, user.otp, user.email)

    app_logger.info(f"New OTP email resent to {email}.")
    return jsonify({'message': 'New OTP has been resent. Please check your inbox.'}), 200