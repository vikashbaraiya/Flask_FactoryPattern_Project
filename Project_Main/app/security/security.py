from flask import request, jsonify
from app.utils.base_logger import BaseLogger

app_logger = BaseLogger(logger_name="AppInitialization").get_logger()

class SecurityHeaders:
    def __init__(self, app):
        """
        Initialize the security headers class and register the necessary hooks.
        """
        self.app = app
        self.app.after_request(self.add_header)  # Register after_request hook
        self.app.before_request(self.verify_csrf_token)  # Register before_request hook

    def verify_csrf_token(self):
        """
        Verify the CSRF token for POST, PUT, DELETE requests.
        Skips the CSRF check for certain routes.
        """
        app_logger.debug(f"Request Endpoint: {request.endpoint}")
        # Skip CSRF check for certain routes
        if request.endpoint in ['auth.login', 'auth.add_role_endpoint', 'static', 'auth.resend', 
                                'auth.verify', 'reset_password', 'auth.verify_password_otp', 
                                'auth.add_user', 'auth.forgot_password_otp_send', "auth.resend_reset_password_otp"]:
            app_logger.debug("Skipping CSRF check for endpoint: %s", request.endpoint)
            return  # Skip CSRF validation for the above routes

        if request.method in ["POST", "PUT", "DELETE"]:
            token = request.headers.get("X-CSRFToken")
            csrf_token_from_cookie = request.cookies.get('csrf_token')
            app_logger.debug("Request CSRF token: %s", token)
            app_logger.debug("Cookies CSRF token: %s", csrf_token_from_cookie)

            if not token or token != csrf_token_from_cookie:
                app_logger.warning("CSRF token mismatch or missing")
                return jsonify({'error': 'Forbidden - invalid CSRF token'}), 403  # Forbidden

    def add_header(self, response):
        """
        Add security-related headers to the response.
        """
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'all'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        app_logger.info("Security headers added to response.")
        return response
