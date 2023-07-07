from pathlib import Path
import json

from_shotn: int = 41095
to_shotn: int = 43220
R_center: float = 410

central: str = ''
all: str = ''
for shotn in range(from_shotn, to_shotn + 1):
    path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\result.json' % shotn)
    if not path.is_file():
        continue
    with open(path, 'r') as file:
        data = json.load(file)
        if 'override' not in data or 't_start' not in data['override'] or 't_stop' not in data['override'] or 'abs_mult' not in data['override']:
            print('no override data')
            continue
        central_ind: int = 0
        for poly in data['config']['poly']:
            if abs(poly['R'] - R_center) < abs(data['config']['poly'][central_ind]['R'] - R_center):
                central_ind = poly['ind']
        print(shotn)
        for event in data['events']:
            if event['error'] is not None:
                continue
            if not data['override']['t_start'] <= event['timestamp'] <= data['override']['t_stop']:
                continue
            for poly_ind in range(len(event['T_e'])):
                poly = event['T_e'][poly_ind]
                if poly['error'] is not None:
                    continue
                if poly['n'] < 0 or poly['Terr'] / poly['T'] > 0.2 or poly['n_err'] / poly['n'] > 0.1:
                    continue
                entry: str = '%.2e, %.2e, %.2e, %.3f\n' % (poly['T'], poly['Terr']/poly['T'], poly['n'], event['energy'])
                all += entry
                if poly_ind == central_ind:
                    central += entry
with open('out/Te(ne)central.csv', 'w') as file:
    file.write(central)
with open('out/Te(ne)all.csv', 'w') as file:
    file.write(all)

print('Code OK')