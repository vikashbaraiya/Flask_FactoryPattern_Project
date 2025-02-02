from datetime import datetime
import re
import time
from sqlite3 import IntegrityError
from typing import OrderedDict
from flask import jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity
import requests
from app.models import Account, BotDetail, BotTradeHistory, Credential, ExchangePair, Performance, User
from app.services.accountservice import AccountService
from app.services.baseservice import BaseService
from app.services.botdataservice import BotDataService
from app.services.botdetailservice import BotDetailService
from app.services.credentialservice import CredentialService
from app.services.exchangepairservice import ExchangePairService
from app.services.external_api_service import ExternalApiService
from app.services.performanceservice import PerformanceService
from app.services.userservice import UserService
from app.services.accountservice import AccountService
from app.utils.base_logger import BaseLogger
from binance import Client
from app.utils.helpers import UtilityHelper
from app.signals.signals import bot_status_changed


app_logger = BaseLogger(logger_name="BotView").get_logger()


# Create humming bot instances and config file
def process_trade_strategy(trade_strategy, strategy_param, bot_name, trade_pair, get_exchange, market_types, controller_config, humming_instance, quote_amount):
    """
    Function to process trade strategy, configure controller, and create Hummingbot instance.
    """
    # Get strategy parameters
    strategy_param, error = ExternalApiService.list_strategy_param(trade_strategy)
    if error:
        return jsonify({"message": error}), 500

    try:
        strategy_param = strategy_param
    except:
        strategy_param = strategy_param[0]['json']
    
    # position_mode ="ONEWAY"
    position_mode = "HEDGE"

    # Extract strategy data and update it
    if trade_strategy in ["dman_maker_v2", "pmm_simple"]:
        str_param = strategy_param['directional_trading'][0][trade_strategy]
        strategy_param['directional_trading'][0][trade_strategy]['id'] = bot_name
        strategy_param['directional_trading'][0][trade_strategy]['trading_pair'] = trade_pair
        strategy_param['directional_trading'][0][trade_strategy]['connector_name'] = get_exchange
        strategy_param['directional_trading'][0][trade_strategy]['total_amount_quote'] = quote_amount
        strategy_param['directional_trading'][0][trade_strategy]['position_mode'] = position_mode
    else:
        str_param = strategy_param['directional_trading'][0][trade_strategy]
        strategy_param['directional_trading'][0][trade_strategy]['id'] = bot_name
        strategy_param['directional_trading'][0][trade_strategy]['trading_pair'] = trade_pair
        strategy_param['directional_trading'][0][trade_strategy]['candles_trading_pair'] = trade_pair
        strategy_param['directional_trading'][0][trade_strategy]['candles_connector'] = get_exchange
        strategy_param['directional_trading'][0][trade_strategy]['connector_name'] = get_exchange
        strategy_param['directional_trading'][0][trade_strategy]['total_amount_quote'] = quote_amount
        strategy_param['directional_trading'][0][trade_strategy]['position_mode'] = position_mode

    # Prepare controller data for submission
    controller = {
        "name": bot_name,
        "content": str_param
    }

    # Post the controller data
    controller_configs, error = ExternalApiService.add_controller_config(controller)
    if error:
        return jsonify({"message": error}), 500

    if controller_configs.get('message') == "Controller configuration uploaded successfully.":
        controller_config_data = {"name": bot_name, "content": controller_config}  # Adjust as necessary
        add_script_ins, error = ExternalApiService.add_script_config(controller_config_data)
        if error:
            return jsonify({"message": error}), 500

        # Check if script configuration was successful
        if add_script_ins.get('message') == "Script configuration uploaded successfully.":
            create_humm_ins, error = ExternalApiService.create_hummingbot_instance(humming_instance)
            if error:
                return jsonify({"message": error}), 500
            app_logger.info("Bot created successfully.")

            # Delete the remaining script
            delete_instance_yml, error = ExternalApiService.delete_yml_hummingbot(bot_name)
            if error:
                app_logger.error(f"Error deleting remaining script: {delete_instance_yml}")
            return {"message": "Instance created successfully", "status": 201}, 201

    return jsonify({"message": "Something went wrong"}), 500

def add_user_bot(data):
    bot_param = data.get("bot_params")
    user_id = bot_param.get('user_id')
    account_id = bot_param.get('account_id')
    credential_id = bot_param.get('credential_id')
    bot_name = bot_param.get('bot_name')
    status = bot_param.get('status', 'active')  # Default status to 'active' if not provided
    # Validate required fields
    if not all([user_id, account_id, credential_id, bot_name]):
        app_logger.info("Missing required fields")
        return jsonify({'message': 'Missing required fields'}), 400
    user = UserService.get_user_by_id(user_id)
    
    # Fetch account and credential details
    credential = Credential.query_active(connector_name=credential_id, user_id=user_id).first()
    if credential is None:
        app_logger.info(f"Credential {credential_id} does not exist or does not belong to user {user_id}.")
        return jsonify({'message': 'Exchange credential does not exist or does not belong to the specified account.'}), 404
    # Check if account and credential are valid
    account = Account.query.filter_by(id=credential.account_id, user_id=user_id).first()
    if account is None:
        app_logger.info(f"Account {account_id} does not belong to user {user_id} or does not exist.")
        return jsonify({'message': 'Exchange account does not belong to user or does not exist.'}), 404

    
    # Check for unique bot name and increment if necessary
    base_bot_name = bot_name.lower()
    current_datetime = datetime.now()
    timestamp = int(current_datetime.timestamp())
    
    bot = BotDetailService.get_bot_detail_by_filters(user_id=user_id, bot_name=bot_name.lower())
    if bot is not None:    
        bot_name = f"{base_bot_name}_{timestamp}"
        
    bot_name = f"{base_bot_name}_{str(timestamp)}"
    controller_config = {"candles_config": [],
			"config_update_interval": 10,
			"controllers_config":
			[f'{bot_name.lower()}.yml'],
			"markets": {},
			"script_file_name": "v2_with_controllers.py",
			"time_to_cash_out": None
			}
    #  Create humming bot instance setting 
    humming_instance = {
        "instance_name": bot_name.lower(),
        "credentials_profile": account.name,
        "image": "hummingbot/hummingbot:latest",
        "script":"v2_with_controllers.py",
        "script_config":f'{bot_name.lower()}.yml'

    }
    #  tradding strategy param and data
    trade_strategy = bot_param['trade_strategy']
    strategy_param = bot_param['strategy_param']
    trade_pair = bot_param['trade_pair']
    get_exchange = bot_param['get_exchange']
    market_types = bot_param['market_types']
    quote_amount = [int(num) for num in re.findall(r'\d+', bot_param['buyAmount'])]
    if quote_amount is None or len(quote_amount)<1:
        return jsonify({"message":"Please provide the qoute amount to buy"}), 200

    process_trade = process_trade_strategy(trade_strategy,
                            strategy_param,bot_name.lower(),
                            trade_pair,
                            get_exchange,
                            market_types, controller_config, humming_instance, quote_amount[0])
    if process_trade[0].get('status')==201:
        # Create and add the new bot detail
        new_bot = BotDetail(user_id=user_id,account_id=account.id,credential_id=credential_id,bot_name=bot_name.lower(),status='running',bot_strategy = trade_strategy, trading_pair=trade_pair)

        BaseService._add_instance(new_bot)
        BaseService._commit_session()
        # add_bot_logs(new_bot)
        time.sleep(5)
        UtilityHelper.general_bot_log(new_bot.bot_name, 'INFO', msg='Bot started successfully...')
        # Trigger signal for bot status change
        # bot_status_changed.send(app, user_email=user.email, bot_name=bot_name, new_status='running')
        return jsonify({
            'message': 'Bot created successfully',
            'bot_name': new_bot.bot_name,
            'status': new_bot.status,
            'created_at': new_bot.created_at,
            'account': {
                'id': account.id,
                'name': account.name
            }
           
        }), 201
    else:
        return jsonify({"message":"Something went wrong"}), 500
    

def get_user_bots_data(user_id):
    # Query for bots associated with the user
    bots = BotDetailService.get_bots_by_filters(user_id=user_id)
    
    # breakpoint()
    if not bots:
        return jsonify({'message': 'No bots found for this user.'}), 404

    # Call the external API
    # external_api_url = f"{conf_bot_url}/get-active-bots-status"
    # headers = {"Content-Type": "application/json"}
    # try:
    #     # time.sleep(6)
    #     response = requests.get(external_api_url, headers=headers)
    #     if response.status_code not in (200, 204):
    #         app.logger.info("Failed to load bot details")
    #         return jsonify({'message': 'Failed to load bot details'}), 400
    # except requests.RequestException:
    #     app.logger.info("Something went wrong")
    #     return jsonify({'message': 'Something went wrong'}), 500
    
    # # Extract keys and values from the external API response
    # external_data = response.json().get("data", {})
    # acount_name = Account.query.filter_by(id=user_id).first()
    # Prepare a dictionary to hold the bot details
    bot_details = {bot.bot_name: {
        'local_data': {
            'id': bot.id,
            'user_id': bot.user_id,
            'account_id': bot.account_id,
            'credential_id': bot.credential_id,
            'bot_name': bot.bot_name,
            'trading_pair': bot.trading_pair,
            'status': bot.status,
            'created_at': bot.created_at.isoformat()  # Format datetime
        },
        'external_data': {}
    } for bot in bots}
    
    # Iterate over the external API response keys
    # for key, value in external_data.items():
    #     # Extract the bot name from the key
    #     bot_name = key.split('-')[1]  # Assuming format is "hummingbot-git_2", get "git_2"
        
    #     if bot_name in bot_details:
    #         # If there's a match, append the external data
    #         bot_details[bot_name]['external_data'] = value
    # Format the response
    response_data = {key: details for key, details in bot_details.items()}
    # res = OrderedDict(reversed(list(response_data.items())))
    # reversed_dict = OrderedDict(sorted(response_data.items(), key=lambda x: int(x[0]), reverse=True))

    return jsonify(response_data), 200


def get_admin_bots_data():
    
    # Query for bots associated with the user
    bots = BotDetail.query.all()
    if not bots:
        return jsonify({'message': 'No bots found for this user.'}), 404

    # Call the external API
    # external_api_url = f"{conf_bot_url}/get-active-bots-status"
    # headers = {"Content-Type": "application/json"}

    # try:
    #     response = requests.get(external_api_url, headers=headers)
    #     if response.status_code not in (200, 204):
    #         app.logger.info("Failed to load bot details")
    #         return jsonify({'message': 'Failed to load bot details'}), 400
    # except requests.RequestException:
    #     app.logger.info("Something went wrong")
    #     return jsonify({'message': 'Something went wrong'}), 500

    # # Extract keys and values from the external API response
    # external_data = response.json().get("data", {})
    
    # Prepare a dictionary to hold the bot details
    bot_details = {bot.bot_name: {
        'local_data': {
            'id': bot.id,
            'user_id': bot.user_id,
            'account_id': bot.account_id,
            'credential_id': bot.credential_id,
            'trading_pair': bot.trading_pair,
            'bot_name': bot.bot_name,
            'status': bot.status,
            'created_at': bot.created_at.isoformat()  # Format datetime
        },
        'external_data': {}
    } for bot in bots}
    
    # Iterate over the external API response keys
    # for key, value in external_data.items():
    #     # Extract the bot name from the key
    #     bot_name = key.split('-')[1]  # Assuming format is "hummingbot-git_2", get "git_2"
        
    #     if bot_name in bot_details:
    #         # If there's a match, append the external data
    #         bot_details[bot_name]['external_data'] = value
    # # Format the response
    response_data = {key: details for key, details in bot_details.items()}
    res = OrderedDict(reversed(list(response_data.items())))

    return jsonify(res), 200



def left_bots_logs_data(bot_name):
    
    # Query for bots associated with the user
    if not bot_name:
        return jsonify({"message":"Bot name is required"}), 400
    
    bots = BotDetail.query.filter_by(bot_name = bot_name).first()    
    if not bots:
        return jsonify({'message': 'No bots found for this user.'}), 404
    # Call the external API
    status_success, external_data = ExternalApiService.get_bot_status(bot_name)

    # Handle the response
    if not status_success:
        # If the request failed, return the error message
        return jsonify({'message': external_data}), 400
    # Iterate over bots and prepare the local data
    bots_data = BotDetail.serialize(bots)
    # Prepare the response data, ordered by user_id
    bots_data.update({"connector_name":bots.credential_id})
    return jsonify({"bot_data":bots_data, "external_data":external_data}), 200



def get_bot_performance_data(user_id, bot_name):
    """
    Fetch bot performance data. If external data is unavailable, fallback to the local database.
    """
    try:
        if not user_id:
            return jsonify({"message": "User ID is required"}), 400
        
        # Fetch the bot details
        # bot = BotDetail.query.filter_by(user_id=user_id, bot_name=bot_name).first()
        bot = PerformanceService.get_performance_by_filter(bot_id=bot.id, bot_name=bot_name)
        if not bot:
            return jsonify({"message": "Bot not found"}), 404

        # Fetch bot status from the external API
        status_success, external_data = ExternalApiService.get_bot_status(bot_name)

        if not status_success:
            # If external API fails, retrieve performance data from the database
            # pre_trade = Performance.query.filter_by(bot_id=bot.id, user_id=user_id).all()
            pre_trade = PerformanceService.get_all_performances_by_filter(bot_id=bot.id, user_id=user_id)
            if pre_trade:
                # Serialize and return the last performance entry
                serialized_trades = Performance.serialize_list(pre_trade)
                if serialized_trades:
                    serialized_trades = serialized_trades[-1]
                return jsonify({"message": "Performance history", "performance_instance": serialized_trades}), 200
            return jsonify({"message": "No performance data available"}), 404

        # Extract performance data from external API response
        data = external_data.get('performance', {}).get(bot_name)
        if data:
            # Extract relevant performance metrics
            performance_data = {
                "close_type_counts": data['performance']['close_type_counts'],
                "global_pnl_pct": data['performance']['global_pnl_pct'],
                "global_pnl_quote": data['performance']['global_pnl_quote'],
                "inventory_imbalance": data['performance']['inventory_imbalance'],
                "open_order_volume": data['performance']['open_order_volume'],
                "realized_pnl_pct": data['performance']['realized_pnl_pct'],
                "realized_pnl_quote": data['performance']['realized_pnl_quote'],
                "unrealized_pnl_pct": data['performance']['unrealized_pnl_pct'],
                "unrealized_pnl_quote": data['performance']['unrealized_pnl_quote'],
                "volume_traded": data['performance']['volume_traded'],
                "status": data.get('status', 'unknown')
            }

            # Save performance data to the database
            performance_instance = Performance(
                bot_id=bot.id,
                user_id=user_id,
                bot_name=bot.bot_name,
                **performance_data
            )
            PerformanceService._add_instance(performance_instance)
            PerformanceService._commit_session()
            # PerformanceService.create_performance(performance_instance)
            return jsonify({"performance_instance": performance_instance.serialize()}), 201
        
        # Handle the case where performance data is unavailable
        return jsonify({"message": "Bot performance data not found"}), 200

    except Exception as e:
        app_logger.error(f"Error in get_bot_performance: {e}", exc_info=True)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    



def get_bot_perform_data(user_id):
    """Helper function to send POST requests and return JSON responses."""
    try:
        if not user_id:
            return jsonify({"message": "User id required"}), 400
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        # For admin
        if user.roles[0].name == 'admin':
            bot = BotDetail.query.all()
            if not bot:
                return jsonify({"message": "Bot not found"}), 404
        else:
            #  for individual user
            bot = BotDetailService.get_bots_by_filters(user_id=user_id)
            if not bot:
                return jsonify({"message": "Bot not found"}), 404
        
        for bt in bot:
            bot_name = bt.bot_name
            success, external_data = ExternalApiService.get_bot_status(bot_name)
            if success:
                data = external_data.get("performance", {}).get(f"hummingbot-{bot_name}", {}).get("performance", {})
                if data and external_data['performance'].values():
                    # Extracting values from the dictionary into variables
                    performance_data = {
                        "close_type_counts": data['performance']['close_type_counts'],
                        "global_pnl_pct": data['performance']['global_pnl_pct'],
                        "global_pnl_quote": data['performance']['global_pnl_quote'],
                        "inventory_imbalance": data['performance']['inventory_imbalance'],
                        "open_order_volume": data['performance']['open_order_volume'],
                        "realized_pnl_pct": data['performance']['realized_pnl_pct'],
                        "realized_pnl_quote": data['performance']['realized_pnl_quote'],
                        "unrealized_pnl_pct": data['performance']['unrealized_pnl_pct'],
                        "unrealized_pnl_quote": data['performance']['unrealized_pnl_quote'],
                        "volume_traded": data['performance']['volume_traded'],
                        "status": data.get('status', 'unknown')
                    }
                    # Check if a Performance instance already exists for this bot and user
                    existing_performance = Performance.query.filter_by(bot_id=bt.id, user_id=user_id).first()
                    if existing_performance:
                        # Update existing record
                        for key, value in performance_data.items():
                            setattr(existing_performance, key, value)
                        BaseService._commit_session()  # Commit the changes to the database
                    else:
                        # Create a new Performance instance
                        performance_instance = Performance(bot_id=bt.id, user_id=user_id, bot_name=bot_name, **performance_data)
                        BaseService._add_instance(performance_instance)
                        BaseService._commit_session()  # Commit the new record to the database
                        
        performs = Performance.query.filter(Performance.bot_id.isnot(None)).all()
        unique_performances = {}        
        for performance in performs:
            if performance.bot_id not in unique_performances:
                unique_performances[performance.bot_id] = performance
        
        # Serialize only the unique last entries
        performance_instance = Performance.serialize_list(unique_performances.values())
        return jsonify({"performance_instance": performance_instance}), 200
         
        # performance_instance = Performance.serialize_list(performs)
        # return jsonify({"performance_instance": performance_instance}), 200

    except Exception as e:
        app_logger.error(f"Error in get_bot_status: {e}", exc_info=True)
        return jsonify({"message": f"An error occurred: {e}"}), 500
  


def get_bot_config_data(bot_name):
    """
    Fetches the configuration details for a bot.
    """
    try:
        success, response_data = ExternalApiService.get_all_controller_configs(bot_name)

        if not success:
            return jsonify({"message": response_data.get("message", "Unknown error occurred")}), 400

        bot_details = BotDetail.query.filter_by(bot_name=bot_name).first()
        if not bot_details:
            return jsonify({"message": "Bot details not found"}), 404

        # Filter the relevant configuration data
        for data in response_data:
            if data['id'].lower() == bot_name.lower():
                return jsonify(data), 200

        return jsonify({"message": "Bot configuration not found"}), 404

    except Exception as e:
        app_logger.error(f"Error in get_bot_config: {str(e)}", exc_info=True)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    

def stop_user_bot(data):
    """
    Handles the stopping of a bot by interacting with the external API.
    """
    try: 
        user_id = get_jwt_identity()
        user = UserService.get_user_by_id(user_id)

        if not user:
            return jsonify({"message": "User not found"}), 404
        
        bot_details = BotDetailService.get_bot_detail_by_filters(bot_name=data.get('bot_name'))
    
        if bot_details and bot_details.status == "running":  

            # Call the stop bot API
            success, response_message = ExternalApiService.stop_bot_api(data.get('bot_name'), data)

            if success:
                # Update bot status in the database
                bot_details.status = "stopped"
                BaseService._commit_session()

                # Serialize bot details and trigger async task
                user_serialize = user.serialize()
                bot_details_serialize = bot_details.serialize()
                bot_status_changed.send(user_email=user.email, bot_name=bot_details_serialize["bot_name"], new_status=bot_details.status)
                UtilityHelper.general_bot_log(bot_details_serialize["bot_name"], 'INFO', msg='Bot stopped successfully...')
                return jsonify(bot_details_serialize), 200

        else:
            return jsonify({"message":"bot is already stopped"}), 400  

    except Exception as e:
        app_logger.error(f"Error in stop_bot: {str(e)}", exc_info=True)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    


def start_user_bot(data):
    
    """Helper function to send POST requests and return JSON responses."""
    try:
        bot_var = f"hummingbot-{data.get('bot_name')}"
        user_id = get_jwt_identity()  
        user = UserService.get_user_by_id(user_id)
        user_serialize = user.serialize()
        bot_details = BotDetailService.get_bot_detail_by_filters(bot_name=data.get('bot_name'))

        # data['bot_name'] = bot_var
        success, response_data = ExternalApiService.start_bot_api(bot_var, data)
        #  if container stopped 
        
        if response_data.get('response').get('status') == 400:            
            success, my_data = ExternalApiService.stop_container_api(bot_var, data)
            #  start container
            if my_data== None:
                time.sleep(3)
                success, my_data = ExternalApiService.start_container_api(bot_var, data)
                if my_data== None:
                    time.sleep(8)
                    bot_details.status = "running"
                    BaseService._commit_session()
                    bot_details_serialize = BotDetail.serialize(bot_details)
                    bot_status_changed.send(user_email=user.email, bot_name=bot_details_serialize["bot_name"], new_status=bot_details.status)  
                    UtilityHelper.general_bot_log(bot_details_serialize["bot_name"], 'INFO', msg='Bot start again successfully...')
                    return jsonify(bot_details_serialize), 200
        # else:
        #     if my_data.get('response').get('status') == 400:
        #         base_url =f"{conf_bot_url}/start-container/{bot_var}"
        #         response = requests.post(base_url, json=data)
        #         my_data = response.json()           
        
        if response_data.get('status')== "success" and response_data.get('response').get("status")== 200 or response_data.get('response').get('status') == 400:               
            bot_details.status = "running"
            BaseService._commit_session()
            bot_details_serialize = BotDetail.serialize(bot_details)
            bot_status_changed.send(user_email=user.email, bot_name=bot_details_serialize["bot_name"], new_status=bot_details.status) 
            UtilityHelper.general_bot_log(bot_details_serialize["bot_name"], 'INFO', msg='Bot start again successfully...')
            return jsonify(bot_details_serialize), 200
        else:
            return jsonify({"message":my_data.get('response').get('msg'), }), 200  
        # breakpoint()
        # if bot_details and bot_details.status == "stopped":
        #     data['bot_name'] = bot_var
        #     base_url =f"{conf_bot_url}/start-bot"
        #     breakpoint()
        #     response = requests.post(base_url, json=data)
        #     my_data = response.json()            
        #     if my_data.get('status')== "success" and my_data.get('response').get("status")== 200:               
        #         bot_details.status = "running"
        #         db.session.commit()
        #         return jsonify(my_data), 200
        #     else:
        #         return jsonify({"message":my_data.get('response').get('msg'), }), 200  
        # else:
        #     return jsonify({"message":"Bot is already start"}), 400  

        
    except Exception as e:
        return jsonify({"message": str(e)}),500
    


def save_trade_history_data(user_id, bot_detail_id):
    """
    Save trade history for a specific user and bot.
    """
    if not user_id:
        return jsonify({"message": "Unauthorized user"}), 401

    # Check if the user and bot exist
    user = UserService.get_user_by_id(user_id) 
    bot = BotDetailService.get_bot_detail_by_filters(user_id=user_id, bot_name=bot_detail_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not bot:
        return jsonify({"error": "Bot not found"}), 404

    try:
        # Fetch trade history using the external API service
        success, response_data = ExternalApiService.get_bot_trade_history(bot_detail_id)
        if not success:
            # Handle cases where the external API call fails
            pre_trade = BotTradeHistory.query.filter_by(bot_detail_id=bot.id).all()
            if pre_trade:
                serialized_trades = BotTradeHistory.serialize_list(pre_trade)
                return jsonify({"message": "Available trade history", "trade_history": serialized_trades}), 200
            return jsonify({"message": "No trade history available"}), 200

        if len(response_data.get('trades'))<1 and response_data.status_code==200:
            pre_trade = BotTradeHistory.query.filter_by(bot_detail_id = bot.id).all()
            if pre_trade:
                # Create and save new trade history entry
                serialized_trades = BotTradeHistory.serialize_list(pre_trade)        
                return jsonify({"message": "Available trade history", "trade_history":serialized_trades}), 200
            else:
                return jsonify({"message": "No trade history"}), 200

        if response_data.get('status') == 200:
            # Process the response data
            trades = response_data.get('trades', [])
            if not trades:
                return jsonify({"message": "No trade history found"}), 404

            for data in trades:
                # Extract and process trade data
                trade_id = data.get('trade_id')
                raw_json = data.get('raw_json')
                market = data.get('market')
                price = data.get('price')
                quantity = data.get('quantity')
                symbol = data.get('symbol')
                trade_timestamp = data.get('trade_timestamp')
                trade_type = data.get('trade_type')
                base_asset = data.get('base_asset')
                quote_asset = data.get('quote_asset')
                pre_trade = BotTradeHistory.query.filter_by(trade_id = trade_id).first()
                if not pre_trade:
                    new_trade_history = BotTradeHistory(
                        user_id=user.id,
                        bot_detail_id=bot.id,
                        raw_json=raw_json,
                        market=market,
                        trade_id=trade_id,
                        price=float(price),
                        quantity=float(quantity),
                        symbol=symbol,
                        trade_timestamp=trade_timestamp,
                        trade_type=trade_type,
                        base_asset=base_asset,
                        quote_asset=quote_asset,
                    )
                    BaseService._add_instance(new_trade_history)
                
            # Commit after processing all trades
            BaseService._commit_session()
            all_trades = BotTradeHistory.query.filter_by(bot_detail_id=bot.id).all()
            serialized_trades = [trade.serialize() for trade in all_trades]
            return jsonify({"message": "Trade history saved successfully", "trade_history": serialized_trades}), 201

        else:
            pre_trade = BotTradeHistory.query.filter_by(bot_detail_id = bot.id).all()
            if pre_trade:
                # Create and save new trade history entry
                serialized_trades = BotTradeHistory.serialize_list(pre_trade)        
            return jsonify({"message": "Available trade history", "trade_history":serialized_trades}), 200

    except Exception as e:
        app_logger.error(f"Error in save_trade_history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500



    
def delete_user_bot_data(data):
    """Delete the bot instance for a specific user."""
    
    user_id, bot_name = data.get('user_id'), data.get('bot_name')
    
    # Check if user_id is provided
    if not user_id:
        app_logger.info("Unauthorized User.")
        return jsonify({"message": "Unauthorized user"}), 401

    # Retrieve the user and bot details
    user = User.query.filter_by(id=user_id).first()
    bot = BotDetail.query.filter_by(bot_name=bot_name, user_id=user.id).first()

    # Check if the user exists
    if not user:
        app_logger.info("User Not Found.")
        return jsonify({'message': "User Not Found."}), 404

    # Check if the bot exists for the user
    if not bot:
        app_logger.info(f"Bot {bot_name} with this detail not found.")
        return jsonify({"message": "Bot detail not found"}), 404

    try:
        # Call the external service to remove the bot container
        success, response_data, status_code = ExternalApiService.remove_bot_container(bot_name)
        # breakpoint()
        # Handle if the API call fails or if response status code is 500
        if status_code == 500:
            # Delete the bot from the database if the external service failed
            # db.session.delete(bot)
            # db.session.commit()
            BotDetailService.delete_bot_detail(bot.id)
            app_logger.info(f"Bot {bot_name} deleted successfully due to external API failure!")
            UtilityHelper.general_bot_log(bot.bot_name, 'INFO', msg='Bot deleted successfully due to API failure.')
            return jsonify({"message": "Bot Deleted successfully"}), 200

        # If the external API indicates success (success flag is True in the response)
        if response_data.get('success') == True:
            # Delete the bot from the database after successful removal
            # db.session.delete(bot)
            # db.session.commit()
            UtilityHelper.general_bot_log(bot.bot_name, 'INFO', msg='Bot deleted successfully.')
            BotDetailService.delete_bot_detail(bot.id)
            app_logger.info(f"Bot {bot_name} deleted successfully!")
            return jsonify({"message": "Bot Deleted successfully"}), 200

        # If the API response does not indicate success
        else:
            app_logger.info(f"Bot {bot_name} is not deleted")
            return jsonify({"message": "Bot is not Deleted"}), 500

    except requests.RequestException as e:
        # Handle external API request failure
        app_logger.error(f"Error while removing bot: {str(e)}")
        return jsonify({"message": f"Request failed: {str(e)}"}), 500

    except Exception as e:
        # Handle any other exceptions
        app_logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"message": str(e)}), 500
    

def delete_user_bot_outside(data):
    """Delete the bot instance for a specific user."""
    user_id, bot_name =data.get('user_id'), data.get('bot_name')
    # if user id is not provided
    if not user_id:
        app_logger.info(f"Unauthorized User.")
        return jsonify({"message": "Unauthorized user"}), 401
    
    user =  UserService.get_user_by_id(user_id)
    bot = BotDetail.query.filter_by(bot_name=bot_name, user_id=user.id).first()
    BotDetailService.get_bot_by_name(user_id, bot_name)
    # if user id is not belong's to any user in database
    if not user:
        app_logger.info(f"User Not Found.")
        return jsonify({'message':"User Not Found."})
    
    # if bot is not belong's to any user
    if not bot:
        app_logger.info(f"Bot {bot_name} with this detail not found")
        return jsonify({"message":"Bot detail not found"})
    
    try:
        BotDetailService.delete_bot_detail(bot.id)
        app_logger.info(f"Bot {bot_name} deleted successfully !")
        return jsonify({"message":"Bot deleted successfully"})
    
    except requests.RequestException as e:
        app_logger.error(f"{str(e)}")
        return jsonify({"message": f"Request failed: {str(e)}"}), 500
    


def update_bot_config(data):
    bot_name = data.get('bot_name')
    controller_id = data.get('controller_id')

    # Check if required fields are present
    if not all([bot_name, controller_id]):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        # Call the external API to update the controller config
        success, response_data = ExternalApiService.update_controller_config(bot_name, controller_id, data.get('config'))

        # If the update failed
        if not success:
            return jsonify({'message': f'Failed to notify external API. {response_data}'}), 400

        # If everything is successful, commit changes to the database
        BaseService._commit_session()
        return jsonify({'message': 'Config updated successfully.'}), 200

    except Exception as e:
        app_logger.error(f"Error occurred: {str(e)}")
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500
    


def get_account_bots(data):
    account_name = data.get('account_name', '')
    credential_id = data.get('credential_id', '')

    # Check request parameter is not empty.
    if not all([account_name,credential_id]):
        return jsonify({'message': 'Missing required fields'}), 400

    # Filter account name 
    account = AccountService.get_accounts_by_account_name(account_name)
    
    # Check account not found in database
    if not account:
        return jsonify({"message":"Account Not Found."})
    # Filter credential 
    credential = CredentialService.get_credential_by_fields(connector_name=credential_id, account_id=account.id)
    
    # Check credential not found in database
    if not credential:
        return jsonify({"message":"Credential Not Found."})
    
    # Filter bot detail belongs to account and credential
    bot_detail = BotDetailService.get_all_bot_details(account_id=account.id, credential_id=credential.connector_name)
    # check bot detail is not empty
    if not bot_detail:
        return jsonify({"message":"bot detail not found."})
    
    return jsonify({"data":[serialize_data.serialize() for serialize_data in bot_detail]})



def fetch_user_bot_data(bot_id):
    """
    Fetch bot data and its associated logs (error and general logs).
    """
    bot = BotDataService.get_bot_data_by_id(bot_id)

    if not bot:
        return jsonify({'error': 'Bot not found'}), 404

    # Serialize bot data including logs
    bot_data = bot.serialize()
    
    return jsonify(bot_data), 200