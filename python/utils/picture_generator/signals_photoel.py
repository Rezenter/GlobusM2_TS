import json

shotn = 44428
poly_ind = '4'

lines = ['time, ch1, err, ch2, err, ch3, err, ch4, err, ch5, err\nms, ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el.\n']
path = '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\signal.json' % shotn
with open(path, 'r') as file:
    data = json.load(file)['data']
    for e in data:
        line = '%.2f, ' % e['timestamp']
        if e['error'] is None:
            for ch in range(5):
                line += '%d, %d, ' % (e['poly'][poly_ind]['ch'][ch]['ph_el'], e['poly'][poly_ind]['ch'][ch]['err'])
            print(line)
            lines.append(line[:-2] + '\n')

with open('signals.csv', 'w') as file:
    file.writelines(lines)

print('Code OK')
