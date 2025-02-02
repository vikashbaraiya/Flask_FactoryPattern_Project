from app.utils.base_logger import BaseLogger
from app.models import GeneralLog
from app.services.baseservice import BaseService
from sqlalchemy.exc import SQLAlchemyError
import logging

# Initialize logger for the service
app_logger = BaseLogger(logger_name="GeneralLogService").get_logger()

class GeneralLogService(BaseService):

    @staticmethod
    def create_general_log(bot_id, level_name, msg, timestamp):
        try:
            return GeneralLogService.create(
                GeneralLog,
                bot_id=bot_id,
                level_name=level_name,
                msg=msg,
                timestamp=timestamp
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating GeneralLog for bot {bot_id}: {e}")
            return None

    @staticmethod
    def get_general_log_by_id(general_log_id):
        try:
            return GeneralLogService.get(GeneralLog, id=general_log_id)
        except SQLAlchemyError as e:
            logging.error(f"Error fetching GeneralLog with id {general_log_id}: {e}")
            return None

    @staticmethod
    def get_general_logs_for_bot(bot_id):
        try:
            return GeneralLogService.get_all(GeneralLog, bot_id=bot_id)
        except SQLAlchemyError as e:
            logging.error(f"Error fetching GeneralLogs for bot {bot_id}: {e}")
            return []

    @staticmethod
    def delete_general_log(general_log_id):
        try:
            return GeneralLogService.delete(GeneralLog, general_log_id)
        except SQLAlchemyError as e:
            logging.error(f"Error deleting GeneralLog with id {general_log_id}: {e}")
            return None
