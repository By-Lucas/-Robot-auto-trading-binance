import  time
import requests
import json
 

def timestamp():
    url = "https://api.binance.com/api/v1/time"
    t = time.time() * 1000
    r = requests.get(url)
    time_stamp = json.loads(r.content)
    return int(time_stamp['serverTime'])

print(timestamp())