import logging
from re import S
import requests
import time
import json

from urllib.parse import urlencode

import hmac
import hashlib

import websocket
import threading


logger = logging.getLogger()


class BinanceFuturesClient:
    
    def __init__(self, public_key, secret_key, testnet):
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
            self.wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self.base_url = "https://fapi.binance.com"
            self.wss_url = "wss://fstream.binance.com/ws"
        
        self.public_key= public_key
        self.secret_key = secret_key

        self.headers = {'X-MBX-APIKEY': self.public_key}

        self.prices = dict()

        self.id = 1
        self.ws = None

        t = threading.Thread(target=self.start_ws)
        t.start()

        logger.info("Binance Futures Client Iniciado com sucesso")


    def timestamp(self):
        url = "https://api.binance.com/api/v1/time"
        t = time.time() * 1000
        r = requests.get(url)
        time_stamp = json.loads(r.content)
        return int(time_stamp['serverTime'])


    def generate_signature(self, data):
        return hmac.new(self.secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()


    def make_request(self, method, endpoints, data):
        if method == "GET":
            response = requests.get(self.base_url + endpoints, params=data, headers=self.headers)
        elif method == "POST":
            response = requests.post(self.base_url + endpoints, params=data, headers=self.headers)
        elif method == "DELETE":
            response = requests.delete(self.base_url + endpoints, params=data, headers=self.headers)
        else:
            ValueError()
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Erro ao fazer %s pedido para %s: %s (Erro de código %s)", 
                        method, endpoints, response.json(), response.status_code)
            return None


    def get_contracts(self):
        """"https://testnet.binancefuture.com/fapi/v1/exchangeInfo"""
        exchange_info = self.make_request("GET", "/fapi/v1/exchangeInfo", None)

        # Dicionario   
        contracts = dict()
        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['pair']] = contract_data

        return contracts
    

    def get_historical_candles(self, symbol, interval):
        data = dict()
        data['symbol'] = symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self.make_request("GET", "/fapi/v1/klines", data)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append([c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])])
        
        return candles

    # Symbol Order Book Ticker
    def get_bind_ask(self, symbol):
        """https://testnet.binancefuture.com/fapi/v1/ticker/bookTicker?symbol=BTCUSDT"""
        data = dict()
        data['symbol'] = symbol
        ob_data = self.make_request("GET", "/fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            if symbol not in self.prices:
                self.prices[symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[symbol]['ask'] = float(ob_data['askPrice'])

        return self.prices[symbol]


    def get_balances(self):
        data = dict()
        data['timestamp'] = self.timestamp()
        data['signature'] = self.generate_signature(data)

        balances = dict()

        account_data = self.make_request("GET", "/fapi/v1/account", data)
        
        if account_data is not None:
            for a in account_data['assets']:
                balances[a['asset']] = a

        return balances
    

    def place_order(self, symbol, side, quantity, order_type, price=None, tif=None):
        
        data = dict()
        data['symbol'] = symbol
        data['side'] = side
        data['quantity'] = quantity
        data['type'] = order_type

        if price is not None:
            data['price'] = price
        
        if tif is not None:
            data['timeInForce'] = tif
        
        data['timestamp'] = self.timestamp()
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request("POST", "/fapi/v1/order", data)

        return order_status


    def cancel_order(self, symbol, order_Id):

        data = dict()
        data['orderId'] = order_Id
        data['symbol'] = symbol
        
        data['timestamp'] = self.timestamp()
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request("DELETE", "/fapi/v1/order", data)

        return order_status


    def get_order_status(self, symbol, order_id):

        data = dict()
        data['timestamp'] = self.timestamp()
        data['symbol'] = symbol
        data['orderId'] = order_id
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request('GET', "/fapi/v1/order", data)

        return order_status


    def start_ws(self):
        self.ws = websocket.WebSocketApp(self.wss_url, on_open=self.on_open, on_close=self.on_close,
                                    on_error=self.on_error, on_message=self.on_message)
        self.ws.run_forever()
        return
    
    def on_open(self, ws):#ws : adiconar na versão mas recente
        logger.info("Binance conexão aberta")
        
        self.subscribe_channel("BTCUSDT")
        return

    def on_close(self, ws):#ws : adiconar na versão mas recente
        logger.warning("Binance Websocket conexão fechada")
        return

    def on_error(self, ws, msg):#ws : adiconar na versão mas recente
        logger.error("Binance conexão error %s", msg)
        return

    def on_message(self, ws, msg):
        print(msg)

    def subscribe_channel(self, symbol):

        data = dict()
        data['method'] = 'SUBSCRIBE'
        data['params'] = []
        data['params'].append(symbol.lower() + "@bookTicker")
        data['id'] =   self.id

        print(data, type(data))
        print(json.dumps(data), type(json.dumps(data)))

        self.ws.send(json.dumps(data))

        self.id += 1
