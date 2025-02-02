import os
import json

conf_bot_url = None
auth_user_type = None

def load_config():
    global conf_bot_url, auth_user_type
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'bot_config.json')

    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            bot_data = json.load(file)
            conf_bot_url = bot_data.get("bot_url")
            auth_user_type = bot_data.get("user_type")

# Load config when the module is imported
load_config()
