from app.utils.base_logger import BaseLogger
from app.models import Role
from app.services.baseservice import BaseService
from sqlalchemy.exc import SQLAlchemyError

app_logger = BaseLogger(logger_name="BaseService").get_logger()


class RoleService(BaseService):

    @staticmethod
    def create_role(name):
        try:
            return RoleService.create(Role, name=name)
        except SQLAlchemyError as e:
            app_logger.error(f"Error creating role {name}: {e}")
            return None

    @staticmethod
    def get_role_by_id(role_id):
        try:
            return RoleService.get(Role, id=role_id)
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching role with id {role_id}: {e}")
            return None

    @staticmethod
    def get_role_by_name(name):
        try:
            return RoleService.get(Role, name=name)
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching role with name {name}: {e}")
            return None

    @staticmethod
    def update_role(role_id, **updates):
        try:
            return RoleService.update(Role, role_id, **updates)
        except SQLAlchemyError as e:
            app_logger.error(f"Error updating role with id {role_id}: {e}")
            return None

    @staticmethod
    def delete_role(role_id):
        try:
            return RoleService.delete(Role, role_id)
        except SQLAlchemyError as e:
            app_logger.error(f"Error deleting role with id {role_id}: {e}")
            return None
