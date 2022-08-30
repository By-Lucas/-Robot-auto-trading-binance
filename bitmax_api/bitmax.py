import requests

def get_contracts():
    contracts = []

    response_object = requests.get('https://www.bitmex.com/api/v1/instrument/active')
    
    for contract in response_object.json():
        contracts.append(contract['symbol'])
    
    return contracts