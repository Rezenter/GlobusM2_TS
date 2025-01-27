import json

shotn = 45607
t_start = 165
t_stop = 270

data = None
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%d\\result.json' % shotn, 'r') as file:
    data = json.load(file)['events']

line = 'time '
for i in range(11):
    line += 'poly%d_Te poly%d_chi2 ' % (i, i)
print(line[:-1])

for e in data:
    if 'timestamp' not in e:
        continue
    if t_start <= e['timestamp'] <= t_stop:
        line = '%.2f ' % e['timestamp']
        for p in e['T_e']:
            if p['error'] is not None:
                line += '-- -- '
            else:
                line += '%.1f %.3f ' % (p['T'], p['chi2'])
        print(line[:-1])

print('Code ok')
