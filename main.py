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

    #binance = BinanceFuturesClient(api_key_futures, api_secret_futures, True)
    #print(binance.get_balances())
    #print(binance.place_order("BTCUSDT", "BUY", 0.01, "LIMIT", 19700.00, "GTC"))
    #print(binance.get_order_status("BTCUSDT", 3205718668))
    #print(binance.cancel_order("BTCUSDT", 3205718668))

    class Interface:

        def __init__(self) -> None:
            self.binance = BinanceFuturesClient(api_key_futures, api_secret_futures, True)


            self.root = tk.Tk()
            self.root.configure(bg='Gray12')
            self.title = self.root.title('Robo TK Binance')
            self.geometry_root = self.root.geometry('700x500')

            self.calibri_font = ("Calibri", 11, "normal")

            self.labels()
            self.root.mainloop()
            

        def labels(self):
            label_title = tk.Label(self.root ,text='Robot Auto trading Binance', font='arial 20', bg='Gray10', fg='white')
            label_title.pack(side=tk.TOP, anchor=tk.CENTER, fill='x')

            label_balance =tk.Label(self.root ,text='Balance: 1000.00 USD', font=self.calibri_font, bg='darkgreen', borderwidth=1, fg='white')
            label_balance.pack(side=tk.TOP, anchor=tk.NW, pady=5)
            
    Interface()