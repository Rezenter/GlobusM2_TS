import json

shotn = 44428

lines = ['time, laser energy El\nms, J\n']
path = '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\result.json' % shotn
with open(path, 'r') as file:
    data = json.load(file)['events']
    for e in data:
        if 'energy' in e:
            line = '%.2f, %.2f' %  (e['timestamp'], e['energy'])
            print(line)
            lines.append(line + '\n')

with open('energy.csv', 'w') as file:
    file.writelines(lines)

print('Code OK')
