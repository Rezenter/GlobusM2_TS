import json
from datetime import datetime

shots = [412, 415, 416, 417, 418, 419, 422]  # 1064
#shots = [414, 420, 421]  # 1047

DB_PATH = 'd:/data/db/debug/signal/'

for shotn in shots:
    print('Processing shot %d' % shotn)
    data = None
    with open('%s%05d.json' % (DB_PATH, shotn), 'r') as file:
        data = json.load(file)
    with open('out/%05d.csv' % shotn, 'w') as file:
        file.write('time, las, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10\n')
        file.write('s, mv*ns, ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el.\n')
        start = data['data'][0]['timestamp']
        for event in data['data']:
            line = '%.4f, %.1f, ' % ((event['timestamp'] - start) * 1e-3, event['laser']['ave']['int'])
            for poly in event['poly']:
                line += '%.1f, ' % event['poly'][poly]['ch'][0]['ph_el']
            file.write(line[:-2] + '\n')
print('Code OK')
