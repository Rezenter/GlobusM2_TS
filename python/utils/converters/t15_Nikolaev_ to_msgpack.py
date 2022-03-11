import msgpack
from pathlib import Path
import json

ch_count = 6
for shotn in range(41604, 41618):
    print(shotn)

    #path = Path('\\\\172.16.12.130\\d\\data\\db\\plasma\\t15\\%d' % shotn)
    path = Path('d:\\data\\db\\plasma\\t15\\%d' % shotn)
    if not path.is_file():
        print('not found')
        continue
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
                event['ch'][ch].append(float(sp[1 + ch]) * 1000)
            if count == 0:
                event['t'] = int(sp[-2])
            count += 1

    while len(data) < 116:
        data.append({
            't': 0,
            'ch': [[0 for cell in range(1024)] for ch in range(ch_count + 1)]
        })

    with open('d:\\data\\db\\plasma\\raw\\%d\\8.msgpk' % shotn, 'wb') as file:
        msgpack.dump(data, file)

    header = ''
    with open('d:\\data\\db\\plasma\\raw\\%d\\header.json' % shotn, 'r') as file:
        header = json.load(file)
        if len(header['boards']) == 8:
            header['boards'].append(15)
    with open('d:\\data\\db\\plasma\\raw\\%d\\header.json' % shotn, 'w') as file:
        json.dump(header, file)
print('Code OK')
