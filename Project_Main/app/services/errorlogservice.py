from app.utils.base_logger import BaseLogger
from app.models import ErrorLog
from app.services.baseservice import BaseService
from sqlalchemy.exc import SQLAlchemyError
import logging

# Initialize logger for the service
app_logger = BaseLogger(logger_name="ErrorLogService").get_logger()

class ErrorLogService(BaseService):

    @staticmethod
    def create_error_log(bot_id, level_name, msg, timestamp):
        try:
            return ErrorLogService.create(
                ErrorLog,
                bot_id=bot_id,
                level_name=level_name,
                msg=msg,
                timestamp=timestamp
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating ErrorLog for bot {bot_id}: {e}")
            return None

    @staticmethod
    def get_error_log_by_id(error_log_id):
        try:
            return ErrorLogService.get(ErrorLog, id=error_log_id)
        except SQLAlchemyError as e:
            logging.error(f"Error fetching ErrorLog with id {error_log_id}: {e}")
            return None

    @staticmethod
    def get_error_logs_for_bot(bot_id):
        try:
            return ErrorLogService.get_all(ErrorLog, bot_id=bot_id)
        except SQLAlchemyError as e:
            logging.error(f"Error fetching ErrorLogs for bot {bot_id}: {e}")
            return []

    @staticmethod
    def delete_error_log(error_log_id):
        try:
            return ErrorLogService.delete(ErrorLog, error_log_id)
        except SQLAlchemyError as e:
            logging.error(f"Error deleting ErrorLog with id {error_log_id}: {e}")
            return None
