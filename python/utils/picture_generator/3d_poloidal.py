import json
from pathlib import Path

shotn: int = 39627
#time: float = 197.8
time: float = 203.8

path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%d\\result.json' % shotn)

data = {
    'main': {},
    'cfm': {}
}
with path.open('r') as f:
    data['main'] = json.load(f)

index_res: int = 999999
for i, e in enumerate(data['main']['events']):
    if 'timestamp' not in e:
        continue
    if time - 0.1 < e['timestamp'] < time + 0.1:
        index_res = i
        break
else:
    fuck

path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%d\\cfm_res.json' % shotn)
with path.open('r') as f:
    data['cfm'] = json.load(f)

index_cfm: int = 999999
for i, e in enumerate(data['cfm']['data']):
    if e['event_index'] == index_res:
        index_cfm = i
        break

for surf in data['cfm']['data'][index_cfm]['data']['surfaces']:
    if surf['a'] == 0:
        print(surf['r'], surf['z'], surf['Te'], surf['ne'], surf['Te'] * surf['ne'])
    else:
        for i in range(len(surf['r'])):
            print(surf['r'][i], surf['z'][i], surf['Te'], surf['ne'], surf['Te'] * surf['ne'])

print('Code OK')
