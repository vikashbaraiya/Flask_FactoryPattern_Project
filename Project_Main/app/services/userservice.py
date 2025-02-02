from app.utils.base_logger import BaseLogger
from app.models import *
from app.services.baseservice import BaseService
from sqlalchemy.exc import SQLAlchemyError


app_logger = BaseLogger(logger_name="BaseService").get_logger()


class UserService(BaseService):

    @staticmethod
    def create_user(first_name, last_name, email, password):
        try:
            user = UserService.create(User, first_name=first_name, last_name=last_name, email=email)
            if user:
                user.set_password(password)
                db.session.commit()  # Commit password hashing separately
                return user
            return None
        except SQLAlchemyError as e:
            app_logger.error(f"Error creating user {email}: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id):
        try:
            return UserService.get(User, id=user_id)
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching user with id {user_id}: {e}")
            return None

    @staticmethod
    def get_user_by_email(email):
        try:
            return UserService.get(User, email=email)
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching user with email {email}: {e}")
            return None

    @staticmethod
    def update_user(user_id, **updates):
        try:
            return UserService.update(User, user_id, **updates)
        except SQLAlchemyError as e:
            app_logger.error(f"Error updating user with id {user_id}: {e}")
            return None

    @staticmethod
    def delete_user(user_id):
        try:
            return UserService.delete(User, user_id)
        except SQLAlchemyError as e:
            app_logger.error(f"Error deleting user with id {user_id}: {e}")
            return None
