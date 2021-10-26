import json
import python.utils.reconstruction.stored_energy as ccm_energy

db_path = 'd:/data/db/plasma/result/'

shots = [
    {
        'shotn': 40796,
        'start_i': 39,
        'stop_i': 91,
        'corr': 1.15
    },
    {
        'shotn': 40797,
        'start_i': 39,
        'stop_i': 89,
        'corr': 1.15
    }
]
for shot in shots:
    with open('out/We_%d.csv' % shot['shotn'], 'w') as out_file:
        header = 'time, We_%d, err, area, n_vol, err, vol\n' % shot['shotn']
        out_file.write(header)

        with open('%s%05d/%05d.json' % (db_path, shot['shotn'], shot['shotn']), 'r') as in_file:
            res = json.load(in_file)
            stored_calc = ccm_energy.StoredCalculator(shot['shotn'], res)
            cfm = stored_calc.calc_dynamics(res['events'][shot['start_i']]['timestamp'], res['events'][shot['stop_i']]['timestamp'], 42)
            if stored_calc.error is not None:
                print(stored_calc.error)
                fuck
            for event_i in range(shot['start_i'], shot['stop_i']):
                event = res['events'][event_i]
                if event['error']:
                    continue
                if event_i != cfm['data'][event_i - shot['start_i']]['event_index']:
                    fuck

                line = '%.1f, ' % event['timestamp']
                line += '%.4f, ' % (0.1 * res['config']['poly'][poly_ind]['R'] - sep_r)

                if poly['error'] and poly['error'] != 'high Te error' and poly['error'] != 'high ne error':
                    line += '--, --, '
                    line += '--, --, '
                else:
                    line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                    line += '%.2e, %.2e, ' % (poly['n'], poly['n_err'])
                out_file.write(line[:-2] + '\n')

print('OK')
