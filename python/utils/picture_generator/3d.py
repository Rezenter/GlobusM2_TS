import json
import os

shotn = 41114
#db = 'd:/data/db/plasma/'
db = '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\'
t_start = 112
correction_mult = 1
t_stop = 256

if not os.path.isdir('%s\\%05d' % (db, shotn)):
    fuck

with open('%s\\%05d\\result.json' % (db, shotn), 'r') as result_fp:
    result = json.load(result_fp)
    if result is not None:
        with open('%s\\%05d\\%05d_3d_Te.csv' % (db, shotn, shotn), 'w') as out_file:
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
        with open('%s\\%05d\\%05d_3d_ne.csv' % (db, shotn, shotn), 'w') as out_file:
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
                            line += '%.3e, ' % (poly['n'] * correction_mult)
                        else:
                            line += '--, '
                    out_file.write(line[:-2] + '\n')
    print('OK')
