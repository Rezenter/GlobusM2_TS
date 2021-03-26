import json

db_path = 'd:/data/db/plasma/result/'

shots = [
    {
        'shotn': 39910,
        'rf': [
            {
                'from': 115,
                'to': 236
            },
        ],
        'from': 115,
        'to': 236
    }
]

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
