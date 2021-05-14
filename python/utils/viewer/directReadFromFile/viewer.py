import ijson
import matplotlib.pyplot as plt

shotn = 406
adc_ind = 0
adc_chs = [
    {
        'gr': 0,
        'ch': 0
    }
]
event_ind = 100

print('Loading raw...')
#with open('d:/data/db/plasma/raw/%05d/%d.json' % (shotn, adc_ind), 'rb') as board_file:
with open('d:/data/db/debug/raw/%05d/%d.json' % (shotn, adc_ind), 'rb') as board_file:
    raw = [[] for ch in range(len(adc_chs))]
    skip = True
    curr = 0
    timestamps = []
    for event in ijson.items(board_file, 'item', use_float=True):
        if skip:
            skip = False
        else:
            timestamps.append(event['groups'][0]['timestamp'])
            plt.plot(range(1024), event['groups'][0]['data'][0])
            plt.show()
            if curr == event_ind:
                print(curr)
                for ch_ind in range(len(adc_chs)):
                    raw[ch_ind] = event['groups'][adc_chs[ch_ind]['gr']]['data'][adc_chs[ch_ind]['ch']]
                break
            else:
                curr += 1
    print('Raw loaded.\n')

plt.plot(range(1024), raw[0])
plt.show()

for cell in range(1024):
    line = ''
    for ch in range(len(adc_chs)):
        line += '%.2f, ' % raw[ch][cell]
    print(line[:-2])
