
from sqlite3 import IntegrityError
from flask import jsonify, request, url_for
import requests
from app.models import Account, AccountExchangeToken, Credential, Exchange, ExchangePair, User
from app.services.accountservice import AccountService
from app.services.baseservice import BaseService
from app.services.botdetailservice import BotDetailService
from app.services.credentialservice import CredentialService
from app.services.exchangepairservice import ExchangePairService
from app.services.external_api_service import ExternalApiService
from app.services.userservice import UserService
from app.services.accountservice import AccountService
from app.utils.base_logger import BaseLogger
from binance import Client

app_logger = BaseLogger(logger_name="AppInitialization").get_logger()

def create_user_account(data):
    account_name = data.get('account_name')
    user_id = data.get('user_id')

    # Validate required fields
    if not account_name or not user_id:
        app_logger.info("Missing required fields")
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if the user exists
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        app_logger.info("User not found")
        return jsonify({'message': 'User not found'}), 404

    # Check if the account name is already in use
    if AccountService.get_accounts_by_account_name(account_name):
        app_logger.info(f"Account name '{account_name}' already exists")
        return jsonify({'message': 'Account name already exists'}), 400

    # Create the new account object (do not commit yet)
    account = Account(name=account_name, user_id=user_id)

    # Using _add_instance to add the account to the session
    if not BaseService._add_instance(account):
        return jsonify({'message': 'Failed to add account to session'}), 500

    try:
        # Call the external API to create the account in the external system
        response, error = ExternalApiService.create_account_to_external_api(account_name)

        if error:
            # External API call failed
            app_logger.error(f"External API call failed: {error}")
            BaseService.rollback_session()  # Rollback on failure
            return jsonify({'message': 'Account created locally, but external API failed'}), 500

        if response.status_code == 201:
            # Commit to the database only if the external API call succeeds
            if not BaseService._commit_session():
                BaseService.rollback_session()  # Rollback if commit fails
                return jsonify({'message': 'Failed to commit session'}), 500

            app_logger.info("Exchange Account created successfully")
            return jsonify({'message': 'Exchange Account created successfully'}), 201

        # Handle unsuccessful API responses
        detail = response.json().get('detail', 'Unknown error')
        app_logger.warning(f"External API error: {detail}")
        BaseService.rollback_session()  # Rollback on external API failure
        return jsonify({'message': detail}), 400

    except IntegrityError:
        BaseService.rollback_session()  # Rollback on database integrity errors
        app_logger.error("Account already exists in the database")
        return jsonify({'message': 'Exchange account already exists'}), 400

    except Exception as e:
        BaseService.rollback_session()  # Rollback on unexpected errors
        app_logger.error(f"Unexpected error: {e}")
        return jsonify({'message': 'An unexpected error occurred'}), 500
    

def delete_user_account(data):
    account_name = data.get('account_name')
    user_id = data.get('user_id')

    if not account_name or not user_id:
        app_logger.info(f"Missing account_name or user_id")
        return jsonify({'message': 'Missing account_name or user_id'}), 400

    # Validate user_id
    user = UserService.get_user_by_id(user_id)
    if not user:
        app_logger.info(f"User not found !")
        return jsonify({'message': 'User not found'}), 404

    # Check if the account belongs to the user
    account = AccountService.get_accounts_by_fields(name=account_name, user_id=user_id)
    if not account:
        app_logger.info(f"Account not found or does not belong to the user")
        return jsonify({'message': 'Account not found or does not belong to the user'}), 404

    # Call the external API to delete the account
    success, message = ExternalApiService.delete_account_to_external_api(account_name)
    if not success:
        return jsonify({'message': message}), 400
    try:
        # Delete related credentials
        AccountService.delete_account_credentials(account.id)
        
        # Delete the account
        AccountService.delete_account(account.id)
        app_logger.info(f"Account deleted successfully.")
        return jsonify({'message': 'Account deleted successfully.'}), 200
    except Exception as e:
        app_logger.warning(f"Error deleting account: {str(e)}")
        return jsonify({'message': str(e)}), 500



# Dynamicaly create pairs for trade
def create_pairs(user_id, exchange_name):
    if not exchange_name in ["binance"]:
        return jsonify({"message":"Exchange pair not created"}), 400
    credential = Credential.query.filter_by(connector_name = 'binance').first() 
    if not credential:
        return jsonify({"message":"No credentials found for pair"}), 404
    
    binance_api_key = credential.details['binance_api_key']
    binance_api_secret = credential.details['binance_api_secret']

    api_key = binance_api_key
    api_secret = binance_api_secret
    exchange_infos = []
    client = Client(api_key, api_secret)
    exchange_info = client.get_exchange_info()
    for s in exchange_info['symbols']:
        exchange_infos.append(s['symbol'])
    
    if exchange_info is not None:
        # Add to the session and commit to the database
        ExchangePairService.create_exchange_pair(ex_pair_list=exchange_infos, exchange_name="binance")
    app_logger.info("Trade available pair save sucessfully")


def add_user_credential(data):
    account_name = data.get('account_name')
    user_id = data.get('user_id')
    connector_name = data.get('connector_name')
    details = data.get('details')  # JSON object for credential details

    if not account_name or not user_id or not connector_name:
        app_logger.info("Missing required fields")
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        # Validate user existence
        user = UserService.get_user_by_id(user_id)
        if not user:
            app_logger.info("User not found")
            return jsonify({'message': 'User not found'}), 404
        
        # Validate account existence
        account = AccountService.get_account_by_fields(name=account_name, user_id=user_id)
        if not account:
            app_logger.info("Account not found or does not belong to the user")
            return jsonify({'message': 'Account not found or does not belong to the user'}), 404

        # Check for existing credentials
        existing_credential = Credential.query_active(connector_name=connector_name, account_id=account.id).first()
        if existing_credential:
            app_logger.info("Credential already exists for the account.")
            return jsonify({'message': 'Credential already exists for the account.'}), 400

        api_data = {}
        for key, value in details.items():
            api_data[key] = data[key]

        # Call the external API
        api_response = ExternalApiService.add_connector_key_external_api(account_name, connector_name, api_data)
        if not api_response.get("success"):
            app_logger.info(api_response["error"])
            return jsonify({'message': api_response["error"]}), 400

        # Add the credential to the database
        credential = Credential(
            user_id=account.user_id,
            connector_name=connector_name,
            details=details,
            account_id=account.id
        )
        BaseService._add_instance(credential)

        try:
            BaseService._commit_session
            create_pairs(account.user_id, connector_name)
        except IntegrityError:
            BaseService.rollback_session()
            app_logger.info("Database IntegrityError: Duplicate credential.")
            return jsonify({'message': 'Credential with this connector already exists for the account.'}), 400

        return jsonify({'message': 'Credential added successfully.'}), 201

    except Exception as e:
        app_logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({'message': str(e)}), 500
    

def list_user_account(user_id):
    
    user = UserService.get_user_by_id(user_id)
    if not user:
        app_logger.info(f"user not found")
        return jsonify({'message': 'User not found'}), 404

    accounts = AccountService.get_accounts_by_user(user_id=user_id)
    # app_logger.info(f"User Accounts list : {accounts}")
    return jsonify([{'account_name': account.name}for account in accounts])


def list_user_credentials(user_id):
    # Check if the user exists
    user = UserService.get_user_by_id(user_id)
    if not user:
        app_logger.info(f"User with ID {user_id} not found")
        return jsonify({'message': 'User not found'}), 404

    # Check if the account exists and belongs to the user
    account = AccountService.get_accounts_by_user(user_id=user_id)
    if not account:
        app_logger.info(f"Account 'Account not found or does not belong to user with ID {user_id}")
        return jsonify({'message': 'Account not found or does not belong to the user'}), 404

    # Retrieve credentials associated with the account
    credentials = Credential.query_active(user_id=user_id).all()
    if not credentials:
        return jsonify({"message":"You don't have any exchange credentials"})
    # Format and return the credentials list
    credential_list = Credential.serialize_list(credentials)
    return jsonify(credential_list), 200


def delete_cred_bot(credential_id, user_id, account_id):
    bots = BotDetailService.get_bots_by_filters(credential_id=credential_id, user_id=user_id, account_id=account_id)
    
    # Check if no bots are found
    if not bots:
        app_logger.info("No bots found with the provided details.")
        return jsonify({"message": "Bot details not found"}), 404
    
    deleted_count = 0
    total_bots = len(bots)
    
    try:
        for bot in bots:
            status_code, response = ExternalApiService.remove_container(bot.bot_name)

            
            if response.status_code == 500:
                app_logger.error(f"Error from server while deleting bot {bot.bot_name}: {response.text}")
            else:
                # Parse the response JSON
                my_data = response.json()
                if my_data.get('success') == True:
                    # Delete the bot record from the database
                    BotDetailService.delete_bot_detail(bot.id)
                    deleted_count += 1
                    app_logger.info(f"Bot {bot.bot_name} deleted successfully!")
                else:
                    app_logger.info(f"Failed to delete bot {bot.bot_name}: {my_data}")
        
        # Check if all bots were successfully deleted
        if deleted_count == total_bots:
            return jsonify({"message": "All bots deleted successfully!"}), 200
        else:
            return jsonify({
                "message": f"{deleted_count}/{total_bots} bots deleted successfully.",
                "failed_count": total_bots - deleted_count
            }), 206  # Partial success
    
    except requests.RequestException as e:
        app_logger.error(f"Request error: {str(e)}")
        return jsonify({"message": f"Request failed: {str(e)}"}), 500
    except Exception as e:
        app_logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"message": str(e)}), 500


def delete_user_credential(data): 
    account_name = data.get('account_name')
    user_id = data.get('user_id')
    connector_name = data.get('connector_name')
    # Check for required fields
    if not account_name or not user_id or not connector_name:
        app_logger.info("Missing required fields")
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        # Check if the user exists
        user = UserService.get_user_by_id(user_id)
        if not user:
            app_logger.info("User not found")
            return jsonify({'message': 'User not found'}), 404

        # Check if the account exists and belongs to the user
        account = AccountService.get_account_by_fields(name=account_name, user_id=user_id)
        if not account:
            app_logger.info("Account not found or does not belong to the user")
            return jsonify({'message': 'Account not found or does not belong to the user'}), 404

        # Locate the credential to delete
        credential = Credential.query_active(
            connector_name=connector_name,
            account_id=account.id
        ).first()
        if not credential:
            app_logger.info("Credential not found")
            return jsonify({'message': 'Credential not found'}), 404

        # Count the number of exchange credentials for the account
        exchange_credentials_count = Credential.query.filter_by(account_id=account.id).count()


        # Check if the account has a default setting
        if account.default:
            # For default accounts, delete the credential via the external API
            success, error_message = ExternalApiService.delete_credential_to_external_api(account_name, connector_name)

            if not success:
                return jsonify({'message': error_message}), 400
            delete_cred_bot(credential.connector_name, user_id, account.id)
            # Delete the credential locally
            credential.soft_delete()
            app_logger.info("Credential deleted successfully.")
            return jsonify({'message': 'Credential deleted successfully.'}), 200

        if exchange_credentials_count > 1:
            # If there are other credentials, just delete the credential locally
            success, error_message = ExternalApiService.delete_credential_to_external_api(account_name, connector_name)

            if not success:
                return jsonify({'message': error_message}), 400
            delete_cred_bot(credential.connector_name, user_id, account.id)
            # Delete the credential locally
            credential.soft_delete()
            app_logger.info("Credential deleted successfully, account remains due to multiple credentials.")
            return jsonify({'message': 'Credential deleted successfully.'}), 200

        # If this is the last credential, also delete the account
        success, error_message = ExternalApiService.delete_account_to_external_api(account_name)
        if not success:
            return jsonify({'message': error_message}), 400
        # If the API call is successful, delete the account and the credential locally
        delete_cred_bot(credential.connector_name, user_id, account.id)
        CredentialService.delete_credential(credential.id)
        AccountService.delete_account(account.id)
        BaseService._commit_session()
        app_logger.info("Credential and account deleted successfully.")
        return jsonify({'message': 'Credential and account deleted successfully.'}), 200

    except Exception as e:
        app_logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({'message': str(e)}), 500
    

def update_user_credential(data):
 
    account_name = data.get('account_name')
    user_id = data.get('user_id')
    connector_name = data.get('connector_name')
    new_details = data.get('new_details')

    if not all([account_name, user_id, connector_name, new_details]):
        return jsonify({'message': 'Missing required fields'}), 400

    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
            
    account = AccountService.get_accounts_by_fields(name=account_name, user_id=user_id)
    if not account:
        return jsonify({'message': 'Account not found or does not belong to the user'}), 404

    credential = Credential.query.filter_by(connector_name=connector_name, account_id=account.id).first()
    if not credential:
        return jsonify({'message': 'Credential not found'}), 404

    for key, value in new_details.items():
        setattr(credential, key, value)

    success, error_message = ExternalApiService.update_credential_to_external_api(account_name, connector_name, new_details)

    if not success:
        return jsonify({'message': error_message}), 400  # Return the error message if the external API call fails

    BaseService._commit_session()
    return jsonify({'message': 'Credential updated successfully.'}), 200



def get_user_accounts_state_data(user_id):
    """
    Retrieve the account state for a specific user by matching their accounts
    """
    try:
        breakpoint()
        # Fetch account state history using the external API service
        success, account_state_data = ExternalApiService.get_account_state_history()
        if not success:
            return jsonify({"message": account_state_data.get("message", "Failed to fetch account state history")}), 500
        # Get all accounts for the specified user
        accounts = AccountService.get_accounts_by_user(user_id=user_id)
        
        if not accounts:
            return jsonify({"message": "User account not found"}), 404

        # Extract the latest state history
        state = account_state_data[-1].get('state', {})
        matched_accounts = []

        # Match user accounts with the state keys
        for account in accounts:
            if account.name in state.keys():
                user_account_data = state[account.name]
                matched_accounts.append({account.name: user_account_data})

        if matched_accounts:
            return jsonify(matched_accounts), 200

        return jsonify({"message": "No matching accounts found"}), 404

    except Exception as e:
        app_logger.error(f"Error in get_user_accounts_state: {e}", exc_info=True)
        return jsonify({"message": str(e)}), 500
    

def get_user_account_data(user_id):
    
    if not user_id:
        return jsonify({"message": "user_id is required"}), 400
    try:
        # Fetch the accounts for the specific user
        accounts = AccountService.get_accounts_by_user(user_id=user_id)
        if not accounts:
            return jsonify({"message": "No accounts found for the specified user"}), 404
        response = []  
        # Iterate over the accounts to gather data
        for account in accounts:
            account_data = {
                account.name: {}
            }
            # Get exchanges for the account
            exchanges = Exchange.query_active(account_id=account.id).all()
            for exchange in exchanges:
                exchange_name = exchange.name
                exchange_data = []
                # Get tokens for the exchange
                account_exchange_tokens = AccountExchangeToken.query_active(account_id=account.id, exchange_id=exchange.id).all()
                for account_exchange_token in account_exchange_tokens:
                    token = account_exchange_token.token
                    exchange_data.append({
                        "token": token.symbol,
                        "units": account_exchange_token.units,
                        "price": token.price,
                        "value": account_exchange_token.value,
                        "available_units": account_exchange_token.available_units
                    })
                # Add the exchange data to the account's response
                account_data[account.name][exchange_name] = exchange_data
            # Add the account data to the response list
            # breakpoint()
            response.append(account_data)
        # Return the response in the desired format
        return jsonify(response)

    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500