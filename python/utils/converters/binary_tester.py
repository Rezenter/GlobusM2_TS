import json

from T15_Nikolaev_to_JSON_v2 import to_json

shotn: int = 1000
data = to_json(shotn=shotn, save_file=True)

with open('tmp.json', 'w') as file:
    json.dump([data[0], data[123], data[333], data[-1]], file)

for event in data:
    print(event['t'])

print('Code OK')
