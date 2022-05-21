import requests
import json
data = {}
with open('testnetwork.json') as f:
    data = json.load(f)

res = requests.post('http://lukasnel.pythonanywhere.com/calculate_capacitance', json=data)
print( res.text)
if res.ok:
    print(res.json())