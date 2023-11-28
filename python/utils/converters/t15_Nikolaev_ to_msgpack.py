import msgpack
from pathlib import Path
import json

ch_count = 5
shots = [43387]
for shotn in shots:
    print(shotn)

    #path = Path('\\\\172.16.12.130\\d\\data\\db\\plasma\\t15\\%d' % shotn)
    path = Path('v:\\data\\db\\plasma\\t15\\raw\\%d\\34\\DRS' % shotn)
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

            adc_channels = [6, 1, 2, 3, 4, 5]
            for ch_ind in range(ch_count + 1):
                event['ch'][ch_ind].append(float(sp[1 + adc_channels[ch_ind]]) * 1000)
            if count == 0:
                event['t'] = int(sp[-2])
            count += 1


    print('THE next line is BAD!!!!!!!!! \n\n\n')
    while len(data) < 101:
        data.append({
            't': 0,
            'ch': [[0 for cell in range(1024)] for ch in range(ch_count + 1)]
        })

    with open('8.msgpk', 'wb') as file:
        msgpack.dump(data, file)

print('Code OK')
