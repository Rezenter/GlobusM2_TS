import json
from pathlib import Path

pub_path: str = '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\'
#spectral_name: str = '\\\\172.16.12.130\\d\\data\\db\\calibration\\expected\\2024.09.16_HFS_noP3c3.json'
spectral_name: str = '\\\\172.16.12.130\\d\\data\\db\\calibration\\expected\\2023.10.06.json'

poly: int = 7
#shots: list[int] = list(range(45846, 45850)) + list(range(45855, 45873))
shots = []
'''
with open('in/request', 'r') as file:
    for line in file:
        shots.append(int(line))
'''

for shotn in range(43470, 44500):
    path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%d\\info.json' % shotn)
    if path.exists():
        with open(path, 'r') as file:
            tmp = json.load(file)
            if tmp['spectral_name'] == '2023.10.06':
                shots.append(shotn)

print(len(shots))

out: dict = {
    'poly': poly,
    'expected': [],
    'measured': []
}
with open(spectral_name, 'r') as file:
    tmp = json.load(file)
    for i in range(len(tmp['T_arr'])):
        out['expected'].append({
            'Te': tmp['T_arr'][i],
            'f': []
        })
        for ch in range(len(tmp['poly'][poly]['expected'])):
            out['expected'][-1]['f'].append(tmp['poly'][poly]['expected'][ch][i])

for shotn in shots:
    #print(shotn)
    path: Path = Path(pub_path + '%d\\result.json' % shotn)
    if not path.exists():
        continue
    res: dict = None
    with open(path, 'r') as file:
        res = json.load(file)
    with open(pub_path + '%d\\signal.json' % shotn, 'r') as file:
        res['sig'] = json.load(file)['data']

    for ev_ind in range(len(res['events'])):
        if 'timestamp' not in res['events'][ev_ind]:
            continue
        if res['override']['t_start'] <= res['events'][ev_ind]['timestamp'] <= res['override']['t_stop']:
            if 'T' not in res['events'][ev_ind]['T_e'][poly]:
                continue
            event = {
                'shotn': shotn,
                'time': res['events'][ev_ind]['timestamp'],
                'Te': res['events'][ev_ind]['T_e'][poly]['T'],
                'Teerr': res['events'][ev_ind]['T_e'][poly]['Terr'],
                'Chi2': res['events'][ev_ind]['T_e'][poly]['chi2'],
                'Nph': [],
                'Npherr': [],

            }
            for ch in range(len(res['sig'][ev_ind]['poly']['%d' % poly]['ch'])):
                if 'ph_el' not in res['sig'][ev_ind]['poly']['%d' % poly]['ch'][ch]:
                    event['Nph'].append(-999)
                    event['Npherr'].append(1e33)
                else:
                    event['Nph'].append(res['sig'][ev_ind]['poly']['%d' % poly]['ch'][ch]['ph_el'])
                    event['Npherr'].append(res['sig'][ev_ind]['poly']['%d' % poly]['ch'][ch]['err'])

            out['measured'].append(event)

with open('chi_poly%d.json' % poly, 'w') as file:
    json.dump(out, file, indent=2)

for ev in out['measured']:
    print(ev['Te'], ev['Chi2'])

print('OK')
