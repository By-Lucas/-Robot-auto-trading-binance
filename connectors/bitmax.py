import requests
import logging
import time
import typing

import hmac
import hashlib
import websocket
import json

from urllib.parse import urlencode

import threading

from models import Balance, Candle, Contract, OrderStatus

logger = logging.getLogger()


class BitmexClient:
    def __init__(self, public_key:str, secret_key:str, testnet:bool):
        if testnet:
            self._base_url = "https://testnet.bitmex.com"
            self._wss_url = "wss://testnet.bitmex.com/realtime"
        else:
            self._base_url = "https://www.bitmex.com"
            self._wss_url = "wss://www.bitmex.com/realtime"

        self._public_key = public_key
        self._secret_key = secret_key

        self._ws =None

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()

        self._ws_id = 1

        # t = threading.Thread(target=self._start_ws)
        # t.start()

        logger.info("Bitmex Client Iniciado com sucesso")

    
    def timestamp(self):
        _url = "https://api.binance.com/api/v1/time"
        t = time.time() * 1000
        r = requests.get(_url)
        time_stamp = json.loads(r.content)
        return int(time_stamp['serverTime'])


    def _generate_signature(self, method: str, endpoint: str, expires: str, data: typing.Dict) -> str:
        message = method + endpoint + "?" + urlencode(data) + expires if len(data) > 0 else method + endpoint + expires
        return hmac.new(self._secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
        

    def _make_request(self, method: str, endpoint: str, data: typing.Dict):
        headres = dict()
        expires =  str(int(time.time()) + 5)
        headres['api-expires'] = expires
        headres['api-key'] = self._public_key
        headres['api-signature'] = self._generate_signature(method, endpoint, expires, data)
        
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=headres)
            except Exception as e:
                logger.error('Erro de conexão ao fazer %s request para %s: %s', method, endpoint, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=headres)
            except Exception as e:
                logger.error('Erro de conexão ao fazer %s request para %s: %s', method, endpoint, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=headres)
            except Exception as e:
                logger.error('Erro de conexão ao fazer %s request para %s: %s', method, endpoint, e)
                return None
        else:
            ValueError()
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Erro ao fazer %s pedido para %s: %s (Erro de código %s)", 
                        method, endpoint, response.json(), response.status_code)
            return None


    def get_contracts(self) -> typing.Dict[str, Contract]:

        instruments = self._make_request("GET", "/api/v1/instrument/active", dict())
        
        contracts = dict()
        if instruments is not None:
            for s in instruments:
                contracts[s['symbol']] = Contract(s, "bitmex")
        return contracts

    
    def get_balances(self) -> typing.Dict[str, Balance]:
        data = dict()
        data['currency'] = "all"

        margin_data = self._make_request("GET", "/api/v1/user/margin", data)

        balances = dict()

        if margin_data is not None:
            for a in margin_data:
                balances[a['currency']] = Balance(a, "bitmex")
        return balances
