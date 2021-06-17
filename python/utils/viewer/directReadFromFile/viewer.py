import ijson
import matplotlib.pyplot as plt

shotn = 40266
adc_ind = 3
adc_chs = [
    {
        'gr': 0,
        'ch': 0
    }
]
event_ind = 66

print('Loading raw...')
with open('d:/data/db/plasma/raw/%05d/%d.json' % (shotn, adc_ind), 'rb') as board_file:
#with open('d:/data/db/debug/raw/%05d/%d.json' % (shotn, adc_ind), 'rb') as board_file:
    raw = [[] for ch in range(len(adc_chs))]
    curr = 0
    timestamps = []
    for event in ijson.items(board_file, 'item', use_float=True):

        if curr >= event_ind:
            timestamps.append(event['groups'][0]['timestamp'])
            print(curr, timestamps[-1], event['groups'][0]['data'][0][0])
            plt.plot(range(1024), event['groups'][0]['data'][0])
            plt.show()
        curr += 1
    print('Raw loaded.\n')

plt.plot(range(1024), raw[0])
plt.show()

