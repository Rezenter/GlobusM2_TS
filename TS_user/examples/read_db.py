import requests
import json

URL = "http://192.168.10.41:8082/api"

shotn = 40458

response = requests.post(url=URL, json={
    'subsystem': 'db',
    'reqtype': 'get_shot',
    'shotn': shotn
})

try:
    data = response.json()
except:
    print('Not a json?')
    fuck

with open('out.json', 'w') as file:
    json.dump(data, file)

print('Code ok')
