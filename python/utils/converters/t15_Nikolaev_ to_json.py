from pathlib import Path
import json

ch_count = 6
shotn = 41604

# ! use only Your own local copy of raw data files!
path = Path('d:\\data\\db\\plasma\\t15\\%d' % shotn)
if not path.is_file():
    print('not found')

data = [{
    't': 0,
    'ch': [[0 for cell in range(1024)] for ch in range(ch_count + 1)]
}]
with path.open(mode='r') as file:
    count = 0
    event = {
        't': 0,
        'ch': [[] for ch in range(ch_count + 1)]
    }
    for line in file:
        if count > 1023:
            count += 1
            if count == 1026:
                data.append(event.copy())
                event = {
                    't': 0,
                    'ch': [[] for ch in range(ch_count + 1)]
                }
                count = 0
            continue
        sp = line.split()

        for ch in range(ch_count + 1):
            event['ch'][ch].append(float(sp[1 + ch]))
        if count == 0:
            event['t'] = int(sp[-2])
        count += 1

with open('test.json', 'w') as file:
    json.dump(data, file)

print('Code OK')
