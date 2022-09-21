import logging
import os

from connectors.binance_futures import BinanceFuturesClient
from connectors.bitmax import BitmexClient

from interface.root_component import Root

from os.path import join, dirname
from dotenv import load_dotenv

# ARQUIVO .env ONDE ARMAZENA DAS INFORMAÇÕES DE SEGURANÇA / CONEXÃO
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

api_key_futures =  os.environ.get("api_key_futures")
api_secret_futures = os.environ.get('api_secret_futures')
api_key_bitmex =  os.environ.get("api_key_bitmex")
api_secret_bitmex = os.environ.get('api_secret_bitmex')


logger = logging.getLogger()

logger.setLevel(logging.DEBUG) #INFO

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

# Cria os logs
file_handler = logging.FileHandler('info.log', encoding='UTF-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)


if __name__ == '__main__':
    binance = BinanceFuturesClient(api_key_futures, api_secret_futures, True)
    bitmex = BitmexClient(api_key_bitmex, api_secret_bitmex, True)
    # print(bitmex.contracts['XBTUSD'].base_asset, bitmex.contracts['XBTUSD'].price_decimals)
    # print(bitmex.balances['XBt'].wallet_balance)
    
    #print(bitmex.place_order(bitmex.contracts['XBTUSD'], "Limit", 100, "Buy", 20000.4939338, "GoodTillCancel"))
    #print(bitmex.get_order_status("9ae96b66-b381-47ad-9941-7ec0ecb6f1e6", bitmex.contracts['XBTUSD']).status)
    #print(bitmex.cancel_order("9ae96b66-b381-47ad-9941-7ec0ecb6f1e6").status)
    #bitmex.get_historical_candles(bitmex.contracts['XBTUSD'], "1h")

    root = Root(binance, bitmex)
    root.mainloop()