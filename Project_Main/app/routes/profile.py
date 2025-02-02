from flask import Blueprint, request, jsonify, session, make_response
from flask_jwt_extended import create_access_token, jwt_required, unset_jwt_cookies
from app.utils.helpers import UtilityHelper
from app.views.profileview import update_user_profile_image, update_user_profile, get_profile_data


profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/update_profile_image', methods=['POST'])
@jwt_required()
def update_profile_image():
    """
    API endpoint to update user profile image.
    """
    return update_user_profile_image()


@profile_bp.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    API endpoint to update user profile.
    """
    data = UtilityHelper.clean_bleach(request.get_json())
    return update_user_profile(data)


@profile_bp.route('/get_profile_details', methods=['GET'])
def get_profile():
    """
    API endpoint to retrieve user profile information.
    """
    return get_profile_data()
