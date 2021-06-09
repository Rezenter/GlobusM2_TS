import json
from datetime import datetime

shots = [
    {
        'caen': 412,
        'ophir': 49
    },
    {
        'caen': 415,
        'ophir': 52
    }
]

DB_PATH = 'd:/data/db/debug/signal/'

with open('out/energy_comp.csv', 'w') as out_file:
    out_file.write('shotn, ophir_time, ophir_E, caen_int\n')
    out_file.write(', ms, mJ, mv*ns\n')
    for shot in shots:
        print('processing shot %d' % shot['caen'])
        with open('%s%05d.json' % (DB_PATH, shot['caen']), 'r') as file:
            caen_data = json.load(file)
        with open('in/959905_%d.txt' % shot['ophir'], 'r') as file:
            ophir_data = []
            for skip_header in range(38):
                file.readline()
            start = None
            for line in file:
                entry = line.split()
                timestamp = datetime.strptime(entry[0], '%H:%M:%S.%f')
                if start is None:
                    start = timestamp
                ophir_data.append({
                    'time': (timestamp - start).microseconds * 0.001,
                    'energy': float(entry[1]) * 1000
                })
        if len(ophir_data) != len(caen_data['data']):
            print(len(ophir_data), len(caen_data['data']))
            fuck
        for i in range(len(ophir_data)):

            out_file.write('%d, %.3f, %.3f, %.1f\n' % (shot['caen'],
                                                           ophir_data[i]['time'], ophir_data[i]['energy'],
                                                       caen_data['data'][i]['laser']['ave']['int']))
print('Code OK')
