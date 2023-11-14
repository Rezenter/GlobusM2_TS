import json

from T15_Nikolaev_to_JSON_v2 import to_json

shotn: int = 2
data = to_json(shotn=shotn, save_file=True)

with open('2.json', 'w') as file:
    json.dump([data[0], data[12], data[3], data[-1]], file, indent=2)

for event in data:
    print(event['t'])

print('Code OK')
