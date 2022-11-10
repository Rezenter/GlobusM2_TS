from T15_Nikolaev_to_JSON_v2 import to_json

shotn: int = 1000
data = to_json(shotn=shotn, save_file=True)
for event in data:
    print(event['t'])

print('Code OK')
