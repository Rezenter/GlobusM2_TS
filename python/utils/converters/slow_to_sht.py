import json
from pathlib import Path
import subprocess

shotn_start: int = 43000
shotn_stop: int = 44000
in_path: str = 'd:/data/db/plasma/slow/raw/'
#out_path = 'd:/data/db/plasma/slow/sht/'
pub_path: str = '//172.16.12.127/Pub/!!!TS_RESULTS/shots/'

#config_file = "d:/data/db/config/2023.07.04_DIVERTOR_G10.json"

for shot in range(shotn_start, shotn_stop):
    folder: Path = Path('//172.16.12.127/Pub/!!!TS_RESULTS/shots/%05d/' % shot)
    if folder.is_dir():
        if not Path('d:/data/db/plasma/slow/raw/sht%05d/' % shot).is_dir():
            print(shot, 'no raw data')
            continue
        info_path: Path = folder.joinpath('info.json')
        with open(info_path, 'r') as info_file:
            info = json.load(info_file)
            config_name: str = info['config_name']
            config: Path = Path('d:/data/db/config/' + config_name + '.json')
            if not config.is_file():
                print(shot, config_name, 'Config not found')
                continue
            print(shot)
            proc = subprocess.run(['d:/code/GTS-cpp/OK_versions/v1.0/executable/SlowADC_to_sht.exe', '%05d' % shot, in_path, str(folder) + '\\', str(config)])
            if proc.returncode != 0:
                print('FUCK')

'''
proc = subprocess.run(['SlowADC_to_sht.exe', '%05d' % shotn, in_path, out_path, config_file])
if proc.returncode != 0:
    print('FUCK')
'''

print('Code ok')