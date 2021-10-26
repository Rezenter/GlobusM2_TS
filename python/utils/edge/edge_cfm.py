import json
import python.utils.reconstruction.stored_energy as ccm_energy

db_path = 'd:/data/db/plasma/result/'

shots = [
    {
        'shotn': 40787,
        'start_i': 44,
        'stop_i': 79
    },
    {
        'shotn': 40793,
        'start_i': 44,
        'stop_i': 80
    },
    {
        'shotn': 40797,
        'start_i': 45,
        'stop_i': 88
    },
    {
        'shotn': 40805,
        'start_i': 45,
        'stop_i': 85
    }
]

polys = [0, 1, 2, 3]

with open('out/cfm_edge.csv', 'w') as out_file:
    header = 'time, edge, '
    for poly in polys:
        header += 'R-edge, T_e, err, n_e, err, '
    out_file.write(header[:-2] + '\n')

    for shot in shots:
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

                surf = cfm['data'][event_i - shot['start_i']]['data']['surfaces'][0]
                for surf_ind in range(len(surf['z']) - 1):
                    if surf['z'][surf_ind] >= 0 > surf['z'][surf_ind + 1] and surf['r'][surf_ind] > 40:
                        sep_r = surf['r'][surf_ind]
                        break
                line = '%.1f, %.2f, ' % (event['timestamp'], sep_r)
                for poly_ind in polys:
                    line += '%.4f, ' % (0.1 * res['config']['poly'][poly_ind]['R'] - sep_r)
                    poly = event['T_e'][poly_ind]
                    if poly['error'] and poly['error'] != 'high Te error' and poly['error'] != 'high ne error':
                        line += '--, --, '
                        line += '--, --, '
                    else:
                        line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                        line += '%.2e, %.2e, ' % (poly['n'], poly['n_err'])
                out_file.write(line[:-2] + '\n')

print('OK')
