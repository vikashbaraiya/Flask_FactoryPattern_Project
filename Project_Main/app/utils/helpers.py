import os
import random
from datetime import datetime
from bleach import clean  # Importing `clean` from bleach for sanitization
from app.models import db, GeneralLog
from app.services.baseservice import BaseService

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class UtilityHelper:
    @staticmethod
    def clean_bleach(data):
        """
        Recursively sanitize strings in a JSON-like dictionary or list.
        """
        if isinstance(data, dict):
            return {key: UtilityHelper.clean_bleach(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [UtilityHelper.clean_bleach(item) for item in data]
        elif isinstance(data, str):
            return clean(data)  # Sanitize strings
        else:
            return data  # Leave other types unchanged

    
    @staticmethod
    def delete_old_file(file_path):
        """
        Delete old file if it exists.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            raise RuntimeError(f"Error deleting file '{file_path}': {str(e)}")

    @staticmethod
    def random_number():
        """
        Generate a random number.
        """
        return random.randint(100000, 999999)
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
