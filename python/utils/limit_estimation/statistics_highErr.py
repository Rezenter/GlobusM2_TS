import json

db_path = 'd:/data/db/plasma/result/'

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

poly_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

with open('error.csv', 'w') as out_fp:
    header = 'n_e, T_e, Te_Err_<20, Te_err_all\n'
    out_fp.write(header)
    header = 'm^-3, eV, %, %\n'
    out_fp.write(header)
    passed = 0
    filtered = 0
    for shot in shots:
        shotn = shot['shotn']
        res = None

        with open('%s%05d/%05d.json' % (db_path, shotn, shotn), 'r') as result_file:
            res = json.load(result_file)
        for event in res['events']:
            if event['error']:
                continue
            #if event['timestamp'] < time[0]:
            if event['timestamp'] < shot['from']:
                continue
            if event['timestamp'] > shot['to']:
                break

            for poly_ind in poly_list:
                poly = event['T_e'][poly_ind]
                if poly['error'] and poly['error'] != 'high Te error' and poly['error'] != 'high ne error':
                    continue
                elif poly['n'] < 1e17 or poly['T'] < 0:
                    continue
                else:
                    err = poly['Terr'] * 100 / poly['T']
                    if err > 20:
                        filtered += 1
                        out_fp.write('%.2f, %.1d, --, %.1d\n' % (poly['n'], poly['T'], err))
                    else:
                        out_fp.write('%.2f, %.1d, %.1d, %.1d\n' % (poly['n'], poly['T'], err, err))
                        passed += 1
                    if poly['n'] < 1e18 and poly['T'] < 50:
                        pass
                        #print('???', shotn, event['timestamp'], poly_ind)
        print(shotn)
print('')
print('passed: %d' % passed)
print('rejected: %d' % filtered)
print('OK')