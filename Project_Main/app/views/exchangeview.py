
import os
from sqlite3 import IntegrityError
from flask import jsonify, request, url_for
from flask_jwt_extended import get_current_user, get_jwt_identity
from app.models import Account, Credential, ExchangePair, User
from app.services.accountservice import AccountService
from app.services.baseservice import BaseService
from app.services.credentialservice import CredentialService
from app.services.exchangepairservice import ExchangePairService
from app.services.external_api_service import ExternalApiService
from app.services.userservice import UserService
from app.services.accountservice import AccountService
from app.utils.base_logger import BaseLogger
from app.utils.helpers import UtilityHelper
from werkzeug.utils import secure_filename
from app.config import Config
from binance import Client

app_logger = BaseLogger(logger_name="ExchangeView").get_logger()


def get_connector_data():
    status_code, response = ExternalApiService.fetch_available_connectors()
    if status_code == 200:
        return jsonify(response), 200
    else:
        return jsonify({'message': response}), status_code
    

def get_connector_map_data(exchange_name):
    """
    Endpoint to fetch the connector configuration map for a specific exchange.
    """
    status_code, response = ExternalApiService.fetch_connector_map(exchange_name)

    if status_code == 200:
        return jsonify(response), 200
    else:
        return jsonify({'message': response}), status_code
    

def verify_user_exchange_pair(exchange_name,pair_name):
    # Get JSON data from the request
    # Validate input data
    if not exchange_name:
        return jsonify({'error': 'Invalid exchange name'}), 400

    if not pair_name:
        return jsonify({'error': 'Invalid pair name'}), 400
    
    # Create a new ExchangePair instance
    new_pair = ExchangePairService.get_exchange_pair_by_filters(exchange_name=exchange_name)
    def verify_pair(pair_name):
        """Check if the trading pair exists in the trading pairs list."""
        return pair_name in new_pair.ex_pair_list
    
    if verify_pair(pair_name):
        if new_pair:
            # # Serialize the created instance
            # result = new_pair.serialize()
            # Return a response
            return jsonify({"message":"Pair available for trade", "data":pair_name, "exchange_name":exchange_name}), 200  # 201 Created
        else:
            return jsonify({"message":"Pair not available for trade"}), 404  # 201 Created
    return jsonify({"message":"Pair not available for trade"}), 404  # 201 Created



def get_exchange_pair():
    
    user_id = get_current_user()
    credential = CredentialService.get_credential_by_fields(user_id = user_id.id, connector_name = 'binance')
    
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
        # Create a new ExchangePair instance
        # new_pair = ExchangePair(
        #     ex_pair_list=exchange_infos,
        #     exchange_name="binance"
        # )
        # # Add to the session and commit to the database
        # db.session.add(new_pair)
        # db.session.commit()
        ExchangePairService.create_exchange_pair(ex_pair_list=exchange_infos, exchange_name="binance")
        # print(s['symbol'])
        return jsonify({"msg":"exchange pair store done..","exchange_pair":exchange_infos}), 200
