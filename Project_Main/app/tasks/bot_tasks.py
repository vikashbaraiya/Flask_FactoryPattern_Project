# app/tasks/bot_tasks.py
import re
from celery import shared_task
from app.models import AccountExchangeToken, BotData, BotDetail, Credential, ErrorLog, Exchange, GeneralLog, Token, db
import requests

from app.services.baseservice import BaseService
from app.services.errorlogservice import ErrorLogService
from app.utils.base_logger import BaseLogger


# Initialize logger for the service
app_logger = BaseLogger(logger_name="TokenService").get_logger()
bot_manager_url = "127.0.0.1:8000"

@shared_task()
def test_task():
    return "Task executed successfully!"

