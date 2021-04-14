import json

db_path = 'd:/data/db/plasma/result/'
poly_list = range(10)

shots = [
    {
        'shotn': 39910,
        'rf': [
        ],
        'from': 118,
        'to': 249
    }, {
        'shotn': 39911,
        'rf': [
            {
                'from': 164,
                'to': 214
            }
        ],
        'from': 118,
        'to': 256
    }, {
        'shotn': 39912,
        'rf': [
        ],
        'from': 118,
        'to': 256
    }, {
        'shotn': 39913,
        'rf': [
            {
                'from': 164,
                'to': 177
            }, {
                'from': 183,
                'to': 196
            }, {
                'from': 202,
                'to': 214
            }

        ],
        'from': 118,
        'to': 256
    }, {
        'shotn': 39914,
        'rf': [
            {
                'from': 163,
                'to': 214
            }
        ],
        'from': 118,
        'to': 256
    }, {
        'shotn': 39915,
        'rf': [
            {
                'from': 163,
                'to': 214
            }
        ],
        'from': 118,
        'to': 250
    }, {
        'shotn': 39916,
        'rf': [
            {
                'from': 163,
                'to': 214
            }
        ],
        'from': 118,
        'to': 254
    }, {
        'shotn': 39917,
        'rf': [
        ],
        'from': 118,
        'to': 253
    }, {
        'shotn': 39918,
        'rf': [
            {
                'from': 163,
                'to': 214
            }
        ],
        'from': 118,
        'to': 250
    }, {
        'shotn': 39919,
        'rf': [
            {
                'from': 164,
                'to': 214
            }
        ],
        'from': 118,
        'to': 253
    }, {
        'shotn': 39920,
        'rf': [
        ],
        'from': 118,
        'to': 250
    }
]
shots = [
    {
        'shotn': 39585,
        'from': 115,
        'to': 236
    }, {
        'shotn': 39586,
        'from': 115,
        'to': 236
    }, {
        'shotn': 39587,
        'from': 115,
        'to': 236
    }, {
        'shotn': 39588,
        'from': 115,
        'to': 245
    }, {
        'shotn': 39589,
        'from': 115,
        'to': 235
    }, {
        'shotn': 39590,
        'from': 115,
        'to': 225
    }, {
        'shotn': 39725,
        'from': 110,
        'to': 215
    }, {
        'shotn': 39726,
        'from': 115,
        'to': 215
    }, {
        'shotn': 39727,
        'from': 115,
        'to': 230
    }, {
        'shotn': 39728,
        'from': 115,
        'to': 170
    }, {
        'shotn': 39729,
        'from': 115,
        'to': 225
    }, {
        'shotn': 39730,
        'from': 115,
        'to': 230
    }, {
        'shotn': 39768,
        'from': 115,
        'to': 230
    },  {
        'shotn': 39769,
        'from': 115,
        'to': 255
    }, {
        'shotn': 39770,
        'from': 115,
        'to': 231
    }, {
        'shotn': 39771,
        'from': 112,
        'to': 213
    }, {
        'shotn': 39772,
        'from': 115,
        'to': 222
    }, {
        'shotn': 39773,
        'from': 115,
        'to': 201
    }, {
        'shotn': 39776,
        'from': 115,
        'to': 140
    }, {
        'shotn': 39781,
        'from': 115,
        'to': 237
    }, {
        'shotn': 39782,
        'from': 111,
        'to': 216
    },
]


ohmic = []
rf = []
totals = [0 for poly_ind in range(len(poly_list))]
ohmic_count = 0
rf_count = 0
for shot in shots:
    shotn = shot['shotn']
    res = None

    with open('%s%05d/%05d.json' % (db_path, shotn, shotn), 'r') as result_file:
        res = json.load(result_file)
    if res is None:
        fuck
    for event in res['events']:
        if event['error']:
            continue
        if event['timestamp'] < shot['from']:
            continue
        if event['timestamp'] > shot['to']:
            break
        is_rf = False
        if 'rf' in shot:
            for interval in shot['rf']:
                if interval['from'] < event['timestamp'] < interval['to']:
                    is_rf = True
                    break
        #print(event['timestamp'], is_rf)
        line = []
        for poly_ind in poly_list:
            poly = event['T_e'][poly_ind]
            if poly['error'] and poly['error'] != 'high Te error' and poly['error'] != 'high ne error':
                line.append(None)
                continue
            elif poly['n'] < 1e17 or poly['T'] < 0:
                line.append(None)
                continue
            line.append(poly['chi2'])
            totals[poly_ind] += 1
        if is_rf:
            rf.append(line)
            rf_count += 1
        else:
            ohmic.append(line)
            ohmic_count += 1
    print(shotn)


with open('chi2_ohmic.csv', 'w') as out_fp:
    for ind in range(len(ohmic)):
        line = ''
        for poly_ind in poly_list:
            if ohmic[ind][poly_ind] is None:
                line += '--, '
            else:
                line += '%.2f, ' % (ohmic[ind][poly_ind])
        out_fp.write(line[:-2] + '\n')

with open('chi2_rf.csv', 'w') as out_fp:
    for ind in range(len(rf)):
        line = ''
        for poly_ind in poly_list:
            if rf[ind][poly_ind] is None:
                line += '--, '
            else:
                line += '%.2f, ' % (rf[ind][poly_ind])
        out_fp.write(line[:-2] + '\n')


print('')
print('ohmic: %d' % ohmic_count)
print('rf: %d' % rf_count)

for poly_ind in range(len(poly_list)):
    print(poly_ind, totals[poly_ind])
print('OK')
