import json

db_path = 'd:/data/db/plasma/'
result_path = 'result/'
signal_path = 'signal/'

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

with open('offscale.csv', 'w') as out_fp:
    header = 'n_e, T_e, err\n'
    out_fp.write(header)
    header = 'm^-3, eV, %\n'
    out_fp.write(header)
    passed = 0
    total = 0
    for shot in shots:
        shotn = shot['shotn']
        res = None
        with open('%s%s%05d/%05d.json' % (db_path, result_path, shotn, shotn), 'r') as result_file:
            res = json.load(result_file)
        sig = None
        with open('%s%s/%05d.json' % (db_path, signal_path, shotn), 'r') as signal_file:
            sig = json.load(signal_file)
        for event_ind in range(len(sig['data'])):
            event = sig['data'][event_ind]
            if event['error']:
                continue
            if event['timestamp'] < shot['from']:
                continue
            if event['timestamp'] > shot['to']:
                break

            for poly_ind in event['poly']:
                poly = event['poly'][poly_ind]
                for ch_ind in range(len(poly['ch'])):
                    if ch_ind > 4:
                        continue
                    ch = poly['ch'][ch_ind]
                    total += 1
                    if ch['error'] and ch['error'].startswith('maximum'):
                        res_event = res['events'][event_ind]['T_e'][int(poly_ind)]
                        te = res_event['T']
                        ne = res_event['n']
                        terr = res_event['Terr']
                        if ne < 4.7e19:
                            print(shotn, event_ind, event['timestamp'], poly_ind, ch_ind, ne)
                        out_fp.write('%.2e, %.1f, %.2f\n' % (ne, te, terr * 100 / te))
                        passed += 1
        print(shotn)
print('')
print('passed: %d' % passed)
print('total: %d' % total)
print('OK')
