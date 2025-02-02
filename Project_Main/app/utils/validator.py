import re
import dns.resolver
from flask import jsonify
# Data Validator Class
class DataValidator:
    # Pass word validator
    @staticmethod
    def validate_password(password):
        # Define password requirements
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):  # At least one uppercase letter
            return False
        if not re.search(r"[a-z]", password):  # At least one lowercase letter
            return False
        if not re.search(r"[0-9]", password):  # At least one digit
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):  # At least one special character
            return False
        return True

    
    @staticmethod
    def is_valid_email(email):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email) is not None

    @staticmethod
    def is_valid_domain(email):
        try:
            domain = email.split('@')[-1]
            dns.resolver.resolve(domain, 'MX')  # Check for MX records
            return True
        except Exception:
            return False

    @staticmethod
    def validate_email(email):
        if not DataValidator.is_valid_email(email):
            return False, "Invalid email format"
        if not DataValidator.is_valid_domain(email):
            return False, "Domain does not exist"
        return True, "Valid email"