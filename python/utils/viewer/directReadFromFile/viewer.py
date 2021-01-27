import ijson
import

shotn = 383
poly = '5'
adc_ind = 1
adc_ch = 11
threshold = 1200/2

print('Loading raw...')
with open('d:/data/db/debug/raw/%05d/%d.json' % (shotn, adc_ind), 'rb') as board_file:
    raw = [[] for ch in range(5)]
    skip = True
    for event in ijson.items(board_file, 'item', use_float=True):
        if skip:
            skip = False
        else:
            for ch
            raw.append(event['groups'][adc_ch // 2]['data'][adc_ch % 2])
    print('Raw loaded.')