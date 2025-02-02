from flask import Blueprint, request, jsonify, session, make_response
from flask_jwt_extended import create_access_token, jwt_required, unset_jwt_cookies
from app.utils.helpers import UtilityHelper
from app.views.authview import add_role, get_user_data, logout_user, resend_otp, signin, signup, get_users_data, verify_otp, forgot_password, verify_forgot_password_otp, resend_reset_otp


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/roles', methods=['POST'])
def add_role_endpoint():
    """
    API endpoint to add a role by calling the add_role function.
    """
    data = request.get_json()
    return add_role(data)

@auth_bp.route('/get-user', methods=['GET'])
@jwt_required()
def get_user_endpoint():
    """
    API endpoint to retrieve user information.
    """
    return get_user_data()


# @auth_bp.route('/users', methods=['GET'])
# @jwt_required()
# def get_users_endpoint():
#     """
#     API endpoint to retrieve all users.
#     """
#     return get_users_data()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = UtilityHelper.clean_bleach(request.get_json())
    return signin(data)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return logout_user()


@auth_bp.route('/users', methods=['POST'])
def add_user():
    data = UtilityHelper.clean_bleach(request.get_json())
    return signup(data)


@auth_bp.route('/verify-otp', methods=['POST'])
def verify():
    data = UtilityHelper.clean_bleach(request.get_json())
    return verify_otp(data)


@auth_bp.route('/resend-otp', methods=['POST'])
def resend():
    data = UtilityHelper.clean_bleach(request.get_json())
    return resend_otp(data)


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password_otp_send():
    data = UtilityHelper.clean_bleach(request.get_json())
    return forgot_password(data)


@auth_bp.route('/verify-password-otp', methods=['POST'])
def verify_password_otp():
    data = UtilityHelper.clean_bleach(request.get_json())
    return verify_forgot_password_otp(data)


@auth_bp.route('/resend-reset-otp', methods=['POST'])
def resend_reset_password_otp():
    data = UtilityHelper.clean_bleach(request.get_json())
    return resend_reset_otp(data)