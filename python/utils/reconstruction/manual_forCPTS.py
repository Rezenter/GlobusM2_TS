from pathlib import Path
import json
import python.utils.reconstruction.stored_energy as ccm



shotn: int = 44433
shift: float = 2
time: float = 179.4
profilesOverrite: str = 'nbi_overrite.csv'
zeff = 2

ts_path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%d\\result.json' % shotn)
ts_data: dict = None
with open(ts_path, 'r') as file:
    ts_data = json.load(file)

override = []
with open('in/%s' % profilesOverrite, 'r') as file:
    file.readline()
    for line in file:
        spl = line.split(',')
        override.append({
            'R': int(spl[0]),
            'T': float(spl[1]),
            'Terr': float(spl[2]),
            'n': float(spl[3]),
            'nerr': float(spl[4])
        })

for i in range(len(ts_data['events'])):
    if 'timestamp' in ts_data['events'][i] and time-0.1 <= ts_data['events'][i]['timestamp'] <= time+0.1:
        ts_data['events'] = [
            {},
            ts_data['events'][i]
        ]
        for i, r in enumerate(ts_data['events'][1]['T_e']):
            r['T'] = override[i]['T']
            r['Terr'] = override[i]['Terr']
            r['n'] = override[i]['n']
            r['n_err'] = override[i]['nerr']
        break

shot_cfm: ccm.StoredCalculator = ccm.StoredCalculator(shotn=shotn, ts_data=ts_data, shift=shift)
cfm_data: dict = shot_cfm.calc_dynamics(t_from=time - 1, t_to=time + 1)['data'][0]['data']


with open('surfaces_%.1f.csv' % time, 'w') as file:
    count: int = 0
    while 1:
        flag: bool = True
        line: str = ''
        for surf in cfm_data['surfaces']:
            if surf['a'] == 0:
                if count == 0:
                    line += '%.3f, %.3f, ' % (surf['r'], surf['z'])
                    flag = False
                else:
                    line += '--, --, '
            else:
                if len(surf['r']) <= count:
                    line += '--, --, '
                else:
                    line += '%.3f, %.3f, ' % (surf['r'][count], surf['z'][count])
                    flag = False
        if flag:
            break
        file.write(line[:-2] + '\n')
        count += 1

data_json = []
data_csv = 'Anrm,Te,ne,Zeff\n'
for surf in cfm_data['surfaces']:
    s = []
    if surf['a'] == 0:
        s.append({
            'R': surf['r']*1e-2,
            'Z': surf['z']*1e-2
        })
    else:
        for i in range(len(surf['r']) - 1, -1, -1):
            s.append({
                'R': surf['r'][i]*1e-2,
                'Z': surf['z'][i]*1e-2
            })
    data_csv += '%.4f,%.3e,%.3e,%.1f\n' % (surf['a'], surf['Te'], surf['ne'], zeff)
    data_json.append(s)
with open('out/surfaces.json', 'w') as file:
    json.dump(data_json, file, indent=2)

with open('out/profiles.csv', 'w') as file:
    file.write(data_csv)

#export data csv

print('Code OK')
