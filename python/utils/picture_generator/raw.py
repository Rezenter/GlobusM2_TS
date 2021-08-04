import ijson

shotn = 40459
adc_ind = 2
adc_chs = [
    {
        'gr': 0,
        'ch': 1
    },    {
        'gr': 1,
        'ch': 0
    },    {
        'gr': 1,
        'ch': 1
    },    {
        'gr': 2,
        'ch': 0
    },    {
        'gr': 2,
        'ch': 1
    },
]  #p0
adc_chs = [
    {
        'gr': 3,
        'ch': 0
    },    {
        'gr': 3,
        'ch': 1
    },    {
        'gr': 4,
        'ch': 0
    },    {
        'gr': 4,
        'ch': 1
    },    {
        'gr': 5,
        'ch': 0
    },
]
'''adc_chs = [
    {
        'gr': 3,
        'ch': 0
    },    {
        'gr': 3,
        'ch': 1
    },    {
        'gr': 4,
        'ch': 0
    },    {
        'gr': 4,
        'ch': 1
    },    {
        'gr': 5,
        'ch': 0
    },
] #p7'''

adc_chs = [
    {
        'gr': 0,
        'ch': 0
    },
    {
        'gr': 0,
        'ch': 1
    }
]

event_ind = 49

print('Loading raw...')
with open('d:/data/db/plasma/raw/%05d/%d.json' % (shotn, adc_ind), 'rb') as board_file:
    raw = [[] for ch in range(len(adc_chs))]
    curr = 0
    for event in ijson.items(board_file, 'item', use_float=True):
        if curr == event_ind:
            for ch_ind in range(len(adc_chs)):
                raw[ch_ind] = event['groups'][adc_chs[ch_ind]['gr']]['data'][adc_chs[ch_ind]['ch']]
            break
        else:
            curr += 1
    print('Raw loaded.\n')


for cell in range(1024):
    line = ''
    for ch in range(len(adc_chs)):
        line += '%.2f ' % raw[ch][cell]
    print(line[:-1])