import json
import ijson
import statistics

shotn = 521
poly_ind = 0

with open('d:/data/db/debug/signal/%05d.json' % shotn, 'r') as data_fp:
    data = json.load(data_fp)
if data is None:
    fuck

adc_ind = data['common']['config']['poly'][poly_ind]['channels'][0]['adc']
adc_ch = data['common']['config']['poly'][poly_ind]['channels'][0]['ch']

print('Loading raw...')
with open('d:/data/db/debug/raw/%05d/%d.json' % (shotn, adc_ind), 'rb') as board_file:
    raw = []
    skip = True
    for event in ijson.items(board_file, 'item', use_float=True):
        if skip:
            skip = False
        else:
            raw.append(event['groups'][adc_ch // 2]['data'][adc_ch % 2])
    print('Raw loaded.')
if len(raw) != len(data['data']):
    print(len(raw))
    print(len(data['data']))
    fuck

with open('debug.json', 'w') as out_fp:
        json.dump(raw[0:2], out_fp)

print('event count = %d\n' % len(data['data']))

delay = []
for event_ind in range(len(raw)):
    #if data['data'][event_ind]['error'] is not None:
    #    continue
    event = data['data'][event_ind]['poly']['%d' % poly_ind]['ch'][0]
    local_threshold = event['zero_lvl'] + (event['max'] - event['min']) * 0.5

    #print(data['data'][event_ind]['laser']['ave']['int'])
    print(event['ph_el'])

    result = 0
    for cell_ind in range(event['from'], event['to']):
        if raw[event_ind][cell_ind] <= local_threshold < raw[event_ind][cell_ind + 1]:
            result = cell_ind + (local_threshold - raw[event_ind][cell_ind]) / \
                     (raw[event_ind][cell_ind + 1] - raw[event_ind][cell_ind])
            break
    if result == 0:
        #print(event)
        #with open('debug.json', 'w') as out_fp:
        #    json.dump(raw[event_ind], out_fp)
        continue
    #print(result, raw[event_ind][cell_ind])
    delay.append(cell_ind / 3.2 - data['data'][event_ind]['laser']['boards'][adc_ind]['sync_ns'])
    #with open('debug.json', 'w') as out_fp:
    #    json.dump(event, out_fp)
    #stop

print('')
print('normal event count = %d' % len(delay))

mean = statistics.mean(delay)
print('mean delay = %.3f' % mean)
print('stdev = %.3f' % statistics.stdev(delay))

centered = [val - mean for val in delay]
maximum = max(centered)
minimum = min(centered)
print('max = %.3f' % maximum)
print('min = %.3f' % minimum)
print('PtP = %.3f' % (maximum - minimum))

print('OK')
