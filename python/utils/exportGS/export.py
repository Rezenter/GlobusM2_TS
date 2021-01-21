import json
import os
import ijson

shots = [39629, 39630]
db = 'd:/data/db/plasma/'
poly_ind = 8  # 5 is good

with open('out/test.csv', 'w') as out_file:
    line = 'shotn, '
    line += 'time, '
    for ch in range(1, 6):
        for cell in range(1024):
            line += 'ch%d_raw_%d, ' % (ch, cell)
        line += 'ch%d_int, ' % ch
        line += 'ch%d_noise, ' % ch
        line += 'ch%d_ph.el., ' % ch
        line += 'ch%d_err, ' % ch
        line += 'ch%d_ok, ' % ch
    line += 'las, '
    line += 'Te, '
    line += 'Te_err, '
    line += 'ne, '
    line += 'ne_err, '
    line += 'chi2, '
    line += 'ok\n'
    out_file.write(line)

    for shotn in shots:
        print('processing %d' % shotn)
        if not os.path.isdir('%sresult/%05d' % (db, shotn)) or \
                not os.path.isfile('%ssignal/%05d.json' % (db, shotn)) or \
                not os.path.isdir('%sraw/%05d' % (db, shotn)):
            fuck

        #result = None
        with open('%sresult/%05d/%05d.json' % (db, shotn, shotn), 'r') as result_fp:
            result = json.load(result_fp)
        if result is not None:
            with open('%ssignal/%05d.json' % (db, shotn), 'r') as signal_fp:
                signal = json.load(signal_fp)
            if signal is not None:
                adc = signal['common']['config']['poly'][poly_ind]['channels']
                adc_ind = adc[0]['adc']
                groups = []
                for ch_ind in range(5):
                    groups.append(adc[ch_ind]['ch'] // 2)
                    if adc_ind != adc[ch_ind]['adc']:
                        fuck
                groups = set(groups)

                #def ch_to_gr(self, ch):
                #    return ch // self.ch_per_group, ch % self.ch_per_group

                raw = [
                    [] for ch in range(5)
                ]
                print('Loadeding raw...')
                with open('%sraw/%05d/%d.json' % (db, shotn, adc_ind), 'rb') as board_file:
                    event_ind = 0
                    for event in ijson.items(board_file, 'item', use_float=True):
                        if event_ind != 0:
                            for ch_ind in range(5):
                                raw[ch_ind].append(event['groups'][adc[ch_ind]['ch'] // 2]['data'][adc[ch_ind]['ch'] % 2])
                        event_ind += 1
                print('Raw loaded.')

                if len(result['events']) != len(signal['data']) and \
                        len(result['events']) != len(raw[0]):
                    fuck
                for event_ind in range(len(result['events'])):
                    res_event = result['events'][event_ind]
                    if res_event['error'] is not None:
                        print(res_event['error'])
                        fuck
                    line = '%d, %.2f, ' % (shotn, res_event['timestamp'])
                    sig_event = signal['data'][event_ind]['poly']['%d' % poly_ind]['ch']
                    for ch_ind in range(5):
                        for cell_ind in range(1024):
                            line += '%.2f, ' % raw[ch_ind][event_ind][cell_ind]
                        line += '%.2f, ' % sig_event[ch_ind]['int']
                        line += '%.2f, ' % sig_event[ch_ind]['pre_std']
                        line += '%.2f, ' % sig_event[ch_ind]['ph_el']
                        line += '%.2f, ' % sig_event[ch_ind]['err']
                        if sig_event[ch_ind]['error']:
                            #print(sig_event[ch_ind]['error'])
                            line += '0, '
                        else:
                            line += '1, '
                    line += '%.2f, ' % (res_event['energy'])
                    if res_event['T_e'][poly_ind]['error'] is None:
                        line += '%.2f, ' % (res_event['T_e'][poly_ind]['T'])
                        line += '%.2f, ' % (res_event['T_e'][poly_ind]['Terr'])
                        line += '%.2f, ' % (res_event['T_e'][poly_ind]['n'])
                        line += '%.2f, ' % (res_event['T_e'][poly_ind]['n_err'])
                        line += '%.2f, ' % (res_event['T_e'][poly_ind]['chi2'])
                        line += '1'
                    else:
                        #print(event['T_e'][poly_ind]['error'])
                        if 'T' in res_event['T_e'][poly_ind]:
                            line += '%.2f, ' % (res_event['T_e'][poly_ind]['T'])
                            line += '%.2f, ' % (res_event['T_e'][poly_ind]['Terr'])
                            line += '%.2f, ' % (res_event['T_e'][poly_ind]['n'])
                            line += '%.2f, ' % (res_event['T_e'][poly_ind]['n_err'])
                            line += '%.2f, ' % (res_event['T_e'][poly_ind]['chi2'])
                        else:
                            line += '-1, '
                            line += '-1, '
                            line += '-1, '
                            line += '-1, '
                            line += '-1, '
                        line += '0'
                    out_file.write(line + '\n')

    print('OK')
