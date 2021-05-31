import json
import math

import integrator
import integration_viewer
import calculator
import relation_fitter

shots = [
    {
        'shotn': 40103,
        'events': [38    , 44    , 50    , 56    , 62    , 68],
        'sync_event': 0,
        'delays': [176.2 , 198.6 , 169.3 , 193.5 , 157.2 , 178.0],
        'is_new': False
    }, {
        'shotn': 40105,
        'events': [39    , 45    , 51    , 57    , 63    , 69   , 75],
        'sync_event': 1,
        'delays': [159.5 , 186.9 , 166.2 , 189.9 , 164.7 , 196.8, 172.9],
        'is_new': False
    }, {
        'shotn': 40106,
        'events': [38    , 44    , 50    , 56    , 62    , 68],
        'sync_event': 1,
        'delays': [148.9 , 183.1 , 160.7 , 186.5 , 171.1 , 200.3],
        'is_new': False
    }, {
        'shotn': 40108,
        'events': [43    , 49    , 55    , 61    , 67],
        'sync_event': 1,
        'delays': [170.0 , 193.2 , 164.9 , 189.9 , 167.5],
        'is_new': False
    }, {
        'shotn': 40109,
        'events': [42, 48, 54, 60, 66],
        'sync_event': 1,
        'delays': [181.2, 160.3, 188.5, 169.8, 191.4],
        'is_new': False
    }
]

shots = [
    {
        'shotn': 40176,
        'is_new': True,
        'start': 122,
        'stop': 218
    }, {
        'shotn': 40175,
        'is_new': True,
        'start': 120,
        'stop': 223
    }, {
        'shotn': 40173,
        'is_new': True,
        'start': 120,
        'stop': 226
    }, {
        'shotn': 40172,
        'is_new': True,
        'start': 126,
        'stop': 234
    }, {
        'shotn': 40171,
        'is_new': True,
        'start': 122,
        'stop': 243
    }, {
        'shotn': 40170,
        'is_new': True,
        'start': 123,
        'stop': 248
    }
]

shots = [ # no glass
    {
        'shotn': 40200,
        'is_new': True,
        'start': 122,
        'stop': 253,
        'config': '2021.05.26_g10_desync2',
        'las_threshold': 40,
        'E1064': 1.5,
        'E1047': 0.9
    }, {
        'shotn': 40201,
        'is_new': True,
        'start': 122,
        'stop': 246,
        'config': '2021.05.26_g10_desync2',
        'las_threshold': 40,
        'E1064': 1.5,
        'E1047': 0.9
    }, {
        'shotn': 40204,
        'is_new': True,
        'start': 125,
        'stop': 246,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }
]

shots = [  # glass
    {
        'shotn': 40205,
        'is_new': True,
        'start': 124,
        'stop': 249,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }, {
        'shotn': 40206,
        'is_new': True,
        'start': 122,
        'stop': 243,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }, {
        'shotn': 40207,
        'is_new': True,
        'start': 121,
        'stop': 249,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }, {
        'shotn': 40208,
        'is_new': True,
        'start': 121,
        'stop': 248,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }, {
        'shotn': 40209,
        'is_new': True,
        'start': 120,
        'stop': 251,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }, {
        'shotn': 40211,
        'is_new': True,
        'start': 121,
        'stop': 249,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }
]

shots = [  # glass
    {
        'shotn': 40208,
        'is_new': True,
        'start': 121,
        'stop': 248,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }, {
        'shotn': 40209,
        'is_new': True,
        'start': 120,
        'stop': 251,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }, {
        'shotn': 40211,
        'is_new': True,
        'start': 121,
        'stop': 249,
        'config': '2021.05.26_g10_sync2',
        'las_threshold': 100,
        'E1064': 0.8,
        'E1047': 0.9
    }
]

#polys = [1, 6]
polys = range(10)

channels = [0, 2, 3, 4]

is_plasma = True

expected_1064 = '2021.05.23'
expected_1047 = '2021.05.18_1047'

expected_1064 = '2021.05.27_1064.4_zs10'
expected_1047 = '2021.05.27_1047.6_zs10'

#expected_1064 = '2021.05.27_1064.4'
#expected_1047 = '2021.05.27_1047.6'

LOCAL_DB_PATH = 'local_db/'
GLOBAL_DB_PATH = 'd:/data/db/'

header = 'shotn, time_47, time_64, ch1_47, err, ch3_47, err, ch4_47, err, ch5_47, err, ch1_64, err, ch3_64, err, ch4_64, err, ch5_64, err, T_64, err, n_64, err, chi2_64, E_64, mult, T_47, err, n_47, err, chi2_47, E_47, mult, T_rel, err, gamma, err, chi2_rel, T_ave, err\n'
units = '#, ms, ms, ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., eV, eV, parr, parr, , J, , eV, eV, parr, parr, , J, , eV, eV, , , , eV, eV\n'

files = []
for poly_ind in range(len(polys)):
    files.append(open('local_db/csv/poly_%d.csv' % polys[poly_ind], 'w'))
    files[poly_ind].write(header)
    files[poly_ind].write(units)

for shot in shots:
    shotn = shot['shotn']

    print('processing shot %d' % shotn)

    raw_processor = integrator.Integrator(LOCAL_DB_PATH, shotn, is_plasma, shot['config'], GLOBAL_DB_PATH)
    raw_processor.process_shot(shot)

    print('\nintegrated.\n')

    fine_processor = calculator.Processor(LOCAL_DB_PATH, shotn, is_plasma, expected_1064, '2021.02.03',
                                          GLOBAL_DB_PATH, expected_1047, shot['E1064'], shot['E1047'])

    resp = fine_processor.get_data()

    print('\ncalculated.\n')

    fitter = relation_fitter.Processor(expected_1064, GLOBAL_DB_PATH, expected_1047)

    for poly_ind_ind in range(len(polys)):
        poly_ind = polys[poly_ind_ind]
        with open('%s/result/%05d/%05d.json' % (LOCAL_DB_PATH, shotn, shotn), 'r') as res_file:
            result = json.load(res_file)
        with open('local_db/csv/%05d_poly#%d.csv' % (shotn, poly_ind), 'w') as file:
            file.write(header)
            file.write(units)

            for event_ind in range(len(result['events'])):
                if 'ts' not in raw_processor.processed[event_ind] or len(raw_processor.processed[event_ind]['ts']) == 1:
                    continue
                if not (shot['start'] <= raw_processor.processed[event_ind]['timestamp'] <= shot['stop']):
                    continue
                if 'error' in raw_processor.processed[event_ind] and raw_processor.processed[event_ind]['error'] != '':
                    continue
                #integration_viewer.draw(shotn, [event_ind], poly_ind)
                line = '%05d, %.1f, %.1f, ' % (shotn, raw_processor.processed[event_ind]['timestamp'], raw_processor.processed[event_ind]['timestamp'])
                for ch in channels:
                    if 'error' in raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch] and raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch]['error'] != '':
                        line += '--, --, '
                        continue
                    line += '%.1f, %.1f, ' % (raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch]['ph_el'] - result['polys'][poly_ind]['stray']['1047'][ch],
                                              raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch]['err'])
                for ch in channels:
                    if 'error' in raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch] and raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch]['error'] != '':
                        line += '--, --, '
                        continue
                    line += '%.1f, %.1f, ' % (raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch]['ph_el'] - result['polys'][poly_ind]['stray']['1064'][ch],
                                              raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch]['err'])
                res_ev = result['events'][event_ind]['ts']['1064']
                t_ave = 0
                w_ave = 0
                ave_err = 0
                if 'T' in res_ev['poly'][poly_ind]:
                    t_ave += res_ev['poly'][poly_ind]['T'] / math.pow(res_ev['poly'][poly_ind]['Terr'], 2)
                    ave_err += res_ev['poly'][poly_ind]['Terr'] / math.pow(res_ev['poly'][poly_ind]['Terr'], 2)
                    w_ave += 1 / math.pow(res_ev['poly'][poly_ind]['Terr'], 2)
                    line += '%.1f, %.1f, %.2e, %.2e, %.2f, %.2f, %.2e, ' % (res_ev['poly'][poly_ind]['T'], res_ev['poly'][poly_ind]['Terr'], res_ev['poly'][poly_ind]['n'], res_ev['poly'][poly_ind]['n_err'], res_ev['poly'][poly_ind]['chi2'], res_ev['energy'], res_ev['poly'][poly_ind]['mult'])
                else:
                    line += '--, --, --, --, --, --, --, '
                res_ev = result['events'][event_ind]['ts']['1047']
                if 'T' in res_ev['poly'][poly_ind]:
                    t_ave += res_ev['poly'][poly_ind]['T'] / math.pow(res_ev['poly'][poly_ind]['Terr'], 2)
                    ave_err += res_ev['poly'][poly_ind]['Terr'] / math.pow(res_ev['poly'][poly_ind]['Terr'], 2)
                    w_ave += 1 / math.pow(res_ev['poly'][poly_ind]['Terr'], 2)
                    line += '%.1f, %.1f, %.2e, %.2e, %.2f, %.2f, %.2e, ' % (res_ev['poly'][poly_ind]['T'], res_ev['poly'][poly_ind]['Terr'], res_ev['poly'][poly_ind]['n'], res_ev['poly'][poly_ind]['n_err'], res_ev['poly'][poly_ind]['chi2'], res_ev['energy'], res_ev['poly'][poly_ind]['mult'])
                else:
                    line += '--, --, --, --, --, --, --, '
                if w_ave != 0:
                    t_ave /= w_ave
                    ave_err /= (w_ave * math.sqrt(2))
                relations = []
                for ch in range(5):
                    if ch not in channels:
                        relations.append({
                            'skip': True
                        })
                        continue
                    if 'error' in raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch] and raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch]['error'] != '':
                        relations.append({
                            'skip': True
                        })
                        continue
                    if 'error' in raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch] and raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch]['error'] != '':
                        relations.append({
                            'skip': True
                        })
                        continue
                    val_1064 = raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch]['ph_el'] - \
                               result['polys'][poly_ind]['stray']['1064'][ch]
                    val_1047 = raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch]['ph_el'] - \
                               result['polys'][poly_ind]['stray']['1047'][ch]
                    relations.append({
                        'val': val_1064 / val_1047
                    })

                    relations[-1]['err'] = relations[-1]['val'] * \
                                           ((raw_processor.processed[event_ind]['ts']['1064'][poly_ind][ch]['err'] /
                                            val_1064) +
                                            (raw_processor.processed[event_ind]['ts']['1047'][poly_ind][ch]['err'] /
                                             val_1047))
                fitted = fitter.calc_temp(relations, poly_ind)
                #print('fitted: ', fitted)
                if 'error' in fitted:
                    line += '--, --, --, --, --, '
                else:
                    line += '%.1f, %.1f, %.2f, %.2f, %.2f, ' % (fitted['T'], fitted['Terr'],
                                                              fitted['gamma'], fitted['g_err'],
                                                              fitted['chi2'])
                line += '%.1f, %.1f\n' % (t_ave, ave_err)
                file.write(line)
                files[poly_ind_ind].write(line)
    print('shot ok\n\n')

for file in files:
    file.close()
print('OK')
