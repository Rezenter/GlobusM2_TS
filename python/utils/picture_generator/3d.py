import json
import os

shotn = 40061
db = 'd:/data/db/plasma/'
t_start = 118
t_stop = 271

if not os.path.isdir('%sresult/%05d' % (db, shotn)):
    fuck

with open('%sresult/%05d/%05d.json' % (db, shotn, shotn), 'r') as result_fp:
    result = json.load(result_fp)
    if result is not None:
        with open('out/%05d_3d_Te.csv' % (shotn), 'w') as out_file:
            line = 'time, '
            for poly in result['config']['poly']:
                line += '%.1f, ' % (poly['R'] * 0.1)
            out_file.write(line[:-2] + '\n')

            for event in result['events']:
                if 'error' in event and event['error'] is not None:
                    print('skipped event: %s' % event['error'])
                    continue
                if t_start < event['timestamp'] < t_stop:
                    line = '%.2f, ' % event['timestamp']
                    for poly in event['T_e']:
                        if 'T' in poly:
                            line += '%.1f, ' % poly['T']
                        else:
                            line += '--, '
                    out_file.write(line[:-2] + '\n')
        with open('out/%05d_3d_ne.csv' % (shotn), 'w') as out_file:
            line = 'time, '
            for poly in result['config']['poly']:
                line += '%.1f, ' % (poly['R'] * 0.1)
            out_file.write(line[:-2] + '\n')

            for event in result['events']:
                if 'error' in event and event['error'] is not None:
                    #print('skipped event: %s' % event['error'])
                    continue
                if t_start < event['timestamp'] < t_stop:
                    line = '%.2f, ' % event['timestamp']
                    for poly in event['T_e']:
                        if 'T' in poly:
                            line += '%.1f, ' % poly['n']
                        else:
                            line += '--, '
                    out_file.write(line[:-2] + '\n')
    print('OK')
