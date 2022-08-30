import tkinter as tk
import logging
import os

#from bitmax_api.bitmax import get_contracts
from connectors.binance_futures import BinanceFuturesClient
from os.path import join, dirname
from dotenv import load_dotenv

# ARQUIVO .env ONDE ARMAZENA DAS INFORMAÇÕES DE SEGURANÇA / CONEXÃO
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

api_key_futures =  os.environ.get("api_key_futures")
api_secret_futures = os.environ.get('api_secret_futures')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG) #INFO

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

# Cria os logs
file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)


if __name__ == '__main__':

    binance = BinanceFuturesClient(api_key_futures, api_secret_futures, True)
    #print(binance.get_balances())
    #print(binance.place_order("BTCUSDT", "BUY", 0.01, "LIMIT", 19700.00, "GTC"))
    #print(binance.get_order_status("BTCUSDT", 3205718668))
    #print(binance.cancel_order("BTCUSDT", 3205718668))


    root = tk.Tk()
    root.configure(bg='Gray12')
    title = root.title('Robo TK Binance')
    tam = root.geometry('500x500')

    calibri_font = ("Calibri", 11, "normal")

    
    root.mainloop()