import logging
import requests
import time
import json
import typing

from urllib.parse import urlencode

import hmac
import hashlib

import websocket
import threading


from models import Balance, Candle, Contract, OrderStatus


logger = logging.getLogger()


class BinanceFuturesClient:
    
    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self.wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = "wss://fstream.binance.com/ws"
        
        self._public_key = public_key
        self._secret_key = secret_key

        self._headers = {'X-MBX-APIKEY': self._public_key}

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()

        self._ws_id = 1
        self._ws = None

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info("Binance Futures Client Iniciado com sucesso")


    def timestamp(self):
        _url = "https://api.binance.com/api/v1/time"
        t = time.time() * 1000
        r = requests.get(_url)
        time_stamp = json.loads(r.content)
        return int(time_stamp['serverTime'])


    def _generate_signature(self, data: typing.Dict) -> str:
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()


    def _make_request(self, method: str, endpoints: str, data: typing.Dict):
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoints, params=data, headers=self._headers)
            except Exception as e:
                logger.error('Erro de conexão ao fazer %s request para %s: %s', method, endpoints, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoints, params=data, headers=self._headers)
            except Exception as e:
                logger.error('Erro de conexão ao fazer %s request para %s: %s', method, endpoints, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoints, params=data, headers=self._headers)
            except Exception as e:
                logger.error('Erro de conexão ao fazer %s request para %s: %s', method, endpoints, e)
                return None
        else:
            ValueError()
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Erro ao fazer %s pedido para %s: %s (Erro de código %s)", 
                        method, endpoints, response.json(), response.status_code)
            return None


    def get_contracts(self) -> typing.Dict[str, Contract]:
        """"https://testnet.binancefuture.com/fapi/v1/exchangeInfo"""
        exchange_info = self._make_request("GET", "/fapi/v1/exchangeInfo", dict())

        # Dicionario   
        contracts = dict()
        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['pair']] = Contract(contract_data, "binance")

        return contracts
    

    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self._make_request("GET", "/fapi/v1/klines", data)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(c))
        
        return candles

    # Symbol Order Book Ticker
    def get_bind_ask(self, contract: Contract) -> typing.Dict[str, float]:
        """https://testnet.binancefuture.com/fapi/v1/ticker/bookTicker?symbol=BTCUSDT"""
        data = dict()
        data['symbol'] = contract.symbol
        ob_data = self._make_request("GET", "/fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])

            return self.prices[contract.symbol]


    def get_balances(self) -> typing.Dict[str, Balance]:
        data = dict()
        data['timestamp'] = self.timestamp()
        data['signature'] = self._generate_signature(data)

        balances = dict()

        account_data = self._make_request("GET", "/fapi/v1/account", data)
        
        if account_data is not None:
            for a in account_data['assets']:
                balances[a['asset']] = Balance(a, "binance")

        return balances
    

    def place_order(self, contract: Contract, side: str, quantity:float, order_type: str, price=None, tif=None) -> OrderStatus:
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side
        data['quantity'] = quantity
        data['type'] = order_type

        if price is not None:
            data['price'] = price
        
        if tif is not None:
            data['timeInForce'] = tif
        
        data['timestamp'] = self.timestamp()
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("POST", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "binance")

        return order_status


    def cancel_order(self, contract: Contract, order_Id: int) -> OrderStatus:
        data = dict()
        data['orderId'] = order_Id
        data['symbol'] = contract.symbol
        
        data['timestamp'] = self.timestamp()
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("DELETE", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "binance")

        return order_status


    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['timestamp'] = self.timestamp()
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request('GET', "/fapi/v1/order", data)

        if order_status is None:
            order_status = OrderStatus(order_status, "binance")

        return order_status


    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self.wss_url, on_open=self._on_open, on_close=self._on_close,
                                    on_error=self._on_error, on_message=self._on_message)
        while True:
            try:
                self.ws.run_forever()
            except Exception as e:
                logger.error("Binance erro em run_forever() metodo: %s", e) 
            time.sleep(2)

    def _on_open(self, ws):#ws : adiconar na versão mas recente
        logger.info("Binance conexão aberta")
        self.subscribe_channel(list(self.contracts.values()), "bookTicker")

    def _on_close(self, ws):#ws : adiconar na versão mas recente
        logger.warning("Binance Websocket conexão fechada")

    def _on_error(self, ws, msg: str):#ws : adiconar na versão mas recente
        logger.error("Binance conexão error %s", msg)

    def _on_message(self, ws, msg: str):#ws : adiconar na versão mas recente
        data = json.loads(msg)

        if "e" in data:
            if data["e"] == "bookTicker":

                symbol = data['s']

                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data['b']), 'ask': float(data['a'])}
                else:
                    self.prices[symbol]['bid'] = float(data['b'])
                    self.prices[symbol]['ask'] = float(data['a'])


    def subscribe_channel(self, contracts: typing.List[Contract], channel: str):
        data = dict()
        data['method'] = 'SUBSCRIBE'
        data['params'] = []

        for contract in contracts:
            data['params'].append(contract.symbol.lower() + "@" + channel)
        data['id']= self._ws_id

        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error('Websocket erro ao assinar %s %s updates: %s', len(contract), channel , e)
            return None

        self._ws_id += 1
