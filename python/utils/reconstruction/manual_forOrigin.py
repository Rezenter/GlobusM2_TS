from pathlib import Path
import json
import python.utils.reconstruction.stored_energy as ccm



shotn: int = 43220
shift: float = 2
time: float = 152.1

ts_path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%d\\result.json' % shotn)
ts_data: dict = None
with open(ts_path, 'r') as file:
    ts_data = json.load(file)

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


print('Code OK')
