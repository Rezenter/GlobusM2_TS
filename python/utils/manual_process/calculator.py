from datetime import datetime
import os
import ijson
import json
import math
import phys_const as const


def calc_chi2(N_i, sigm2_i, f_i):
    res = 0
    top_sum = 0
    bot_sum = 0
    for ch in range(len(N_i)):
        top_sum += (N_i[ch] * f_i[ch]) / sigm2_i[ch]
        bot_sum += math.pow(f_i[ch], 2) / sigm2_i[ch]
    for ch in range(len(N_i)):
        res += math.pow(N_i[ch] - (top_sum * f_i[ch] / bot_sum), 2) / sigm2_i[ch]
    return res


def interpolate(x1, x, x2, y1, y2):
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


class Processor:
    PLASMA_FOLDER = 'plasma/'
    DEBUG_FOLDER = 'debug/'
    SIGNAL_FOLDER = 'signal/'
    RESULT_FOLDER = 'result/'
    EXPECTED_FOLDER = 'calibration/expected/'
    ABSOLUTE_FOLDER = 'calibration/abs/processed/'
    HEADER_FILE = 'header'
    FILE_EXT = '.json'

    cross_section = (8.0 * math.pi / 3.0) * \
                    math.pow((math.pow(const.q_e, 2) / (4 * math.pi * const.eps_0 * const.m_e * math.pow(const.c, 2))), 2)

    def __init__(self, db_path, shotn, is_plasma, expected_id, absolute_id, global_db, expected_aux):
        self.shotn = shotn
        self.is_plasma = is_plasma
        self.expected_id = expected_id
        self.absolute_id = absolute_id
        self.error = None
        if not os.path.isdir(db_path):
            self.error = 'Database path not found.'
            print(self.error)
            return
        self.db_path = db_path
        if not os.path.isdir(global_db):
            self.error = 'Global database path not found.'
            return
        if not os.path.isdir('%s%s' % (global_db, self.EXPECTED_FOLDER)):
            self.error = 'Spectral calibration path not found.'
            print(self.error)
            return
        expected_full_name = '%s%s%s%s' % (global_db, self.EXPECTED_FOLDER, self.expected_id, self.FILE_EXT)
        if not os.path.isfile(expected_full_name):
            self.error = 'Calibration file not found.'
            print(self.error)
            return
        self.expected = {
            '1064': {},
            '1047': {}
        }
        with open(expected_full_name, 'r') as expected_file:
            obj = ijson.kvitems(expected_file, '', use_float=True)
            for k, v in obj:
                self.expected['1064'][k] = v
        with open('%s%s%s%s' % (global_db, self.EXPECTED_FOLDER, expected_aux, self.FILE_EXT), 'r') as expected_file:
            obj = ijson.kvitems(expected_file, '', use_float=True)
            for k, v in obj:
                self.expected['1047'][k] = v
        self.expected['1064']['modification'] = os.path.getmtime(expected_full_name)

        if not os.path.isdir('%s%s' % (global_db, self.ABSOLUTE_FOLDER)):
            self.error = 'Spectral calibration path not found.'
            print(self.error)
            return
        absolute_full_name = '%s%s%s%s' % (global_db, self.ABSOLUTE_FOLDER, self.absolute_id, self.FILE_EXT)
        if not os.path.isfile(absolute_full_name):
            self.error = 'Calibration file not found.'
            print(self.error)
            return
        self.absolute = {}
        with open(absolute_full_name, 'r') as absolute_file:
            obj = ijson.kvitems(absolute_file, '', use_float=True)
            for k, v in obj:
                self.absolute[k] = v
        self.absolute['modification'] = os.path.getmtime(absolute_full_name)

        self.signal = {}
        self.result = {}
        self.load()

    def get_data(self):
        err = self.get_error()
        if err is None:
            return self.result
        else:
            return {
                'error': err
            }

    def get_error(self):
        tmp = self.error
        self.error = None
        return tmp

    def load(self):
        self.result = {}
        self.load_signal()
        if self.error is None:
            self.process_shot()

    def load_signal(self):
        print('loading signal...')
        signal_path = '%s%s%05d%s' % (self.db_path, self.SIGNAL_FOLDER, self.shotn, self.FILE_EXT)
        if not os.path.isfile(signal_path):
            self.error = 'No signal file.'
            return
        with open(signal_path, 'r') as signal_file:
            obj = ijson.kvitems(signal_file, '', use_float=True)
            for k, v in obj:
                self.signal[k] = v

    def process_shot_old(self):
        self.result = {
            'timestamp': datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            'spectral_name': self.expected_id,
            'spectral_mod': datetime.fromtimestamp(self.expected[0]['modification']).strftime('%Y.%m.%d %H:%M:%S'),
            'absolute_name': self.absolute_id,
            'absolute_mod': datetime.fromtimestamp(self.absolute['modification']).strftime('%Y.%m.%d %H:%M:%S'),
            'signal_mod': datetime.fromtimestamp(
                os.path.getmtime('%s%s%05d%s' % (self.db_path, self.SIGNAL_FOLDER, self.shotn, self.FILE_EXT))).
                strftime('%Y.%m.%d %H:%M:%S'),
            'config_name': self.signal['common']['config_name'],
            'polys': []
        }
        print('Processing shot...')

        laser_wl = ['1064', '1047']
        for wl_ind in range(len(laser_wl)):
            wl = laser_wl[wl_ind]
            print('calculating wl = %s...' % wl)
            self.result[wl] = []
            stray = [
                [0.0 for ch in range(5)] for poly in range(10)
            ]
            count = [
                [0 for ch in range(5)] for poly in range(10)
            ]
            if len(self.signal['data']) == 0:
                print('No events!')
                return

            for event_index in range(len(self.signal['data'])):
                if 'error' in self.signal['data'][event_index] and self.signal['data'][event_index]['error'] is not None:
                    print('woops: %s, event #' % self.signal['data'][event_index]['error'], event_index)
                else:
                    if self.signal['data'][event_index]['timestamp'] >= 100:
                        break
                    event = self.signal['data'][event_index]
                    if 'error' in event and event['error'] is not None:
                        continue
                    if 'sync' in event and event['sync']:
                        continue

                    for poly_ind in range(len(event[wl])):
                        for ch_ind in range(len(event[wl][poly_ind])):
                            if event[wl][poly_ind][ch_ind]['error'] is not None:
                                continue
                            count[poly_ind][ch_ind] += 1
                            stray[poly_ind][ch_ind] += event[wl][poly_ind][ch_ind]['ph_el']

            for poly_ind in range(len(stray)):
                for ch_ind in range(len(stray[poly_ind])):
                    if count[poly_ind][ch_ind] > 0:
                        stray[poly_ind][ch_ind] /= count[poly_ind][ch_ind]
                self.result['polys'].append({
                    'ind': self.signal['common']['config']['poly'][poly_ind]['ind'],
                    'fiber': self.signal['common']['config']['poly'][poly_ind]['fiber'],
                    'R': self.signal['common']['config']['poly'][poly_ind]['R'],
                    'l05': self.signal['common']['config']['poly'][poly_ind]['l05'],
                    'h': self.signal['common']['config']['poly'][poly_ind]['h'],
                    'stray': stray[poly_ind]
                })

            for event_ind in range(len(self.signal['data'])):
                error = None
                if self.signal['data'][event_ind]['error'] is not None:
                    self.result[wl].append({
                        'error': self.signal['data'][event_ind]['error']
                    })
                    continue
                proc_event = {
                    'timestamp': self.signal['data'][event_ind]['timestamp'],
                    'energy': self.signal['data'][event_ind]['laser']['ave']['int'] * self.expected[0]['J_from_int']
                }
                if self.signal['data'][event_ind]['error'] is not None:
                    error = self.signal['data'][event_ind]['error']
                else:
                    poly = []
                    energy = self.expected[0]['J_from_int'] * self.signal['data'][event_ind]['laser']['ave']['int']

                    for poly_ind in range(len(self.signal['data'][event_ind][wl])):
                        temp = self.calc_temp(self.signal['data'][event_ind][wl][poly_ind], poly_ind,
                                              stray[poly_ind], energy, wl_ind)
                        poly.append(temp)
                    proc_event['T_e'] = poly
                proc_event['error'] = error
                self.result[wl].append(proc_event)
            print('done\n\n')
        self.save_result()

    def calc_stray(self):
        result = {
            '1064':  [[{
                'stray': 0.0,
                'count': 0
            } for ch in range(5)] for poly in range(10)],
            '1047': [[{
                'stray': 0.0,
                'count': 0
            } for ch in range(5)] for poly in range(10)]
        }

        for event_index in range(len(self.signal['data'])):
            if 'error' in self.signal['data'][event_index] and self.signal['data'][event_index]['error'] is not None:
                print('woops: %s, event #' % self.signal['data'][event_index]['error'], event_index)
            else:
                if self.signal['data'][event_index]['timestamp'] >= 100:
                    break
                event = self.signal['data'][event_index]
                if 'sync' in event and event['sync']:
                    continue

                for wl in event['ts'].keys():
                    for poly_ind in range(len(event['ts'][wl])):
                        for ch_ind in range(len(event['ts'][wl][poly_ind])):
                            if event['ts'][wl][poly_ind][ch_ind]['error'] is not None:
                                continue
                            result[wl][poly_ind][ch_ind]['count'] += 1
                            result[wl][poly_ind][ch_ind]['stray'] += event['ts'][wl][poly_ind][ch_ind]['ph_el']

        if len(self.signal['data']) != 0:
            for poly_ind in range(10):
                entry = {
                    'ind': self.signal['common']['config']['poly'][poly_ind]['ind'],
                    'fiber': self.signal['common']['config']['poly'][poly_ind]['fiber'],
                    'R': self.signal['common']['config']['poly'][poly_ind]['R'],
                    'l05': self.signal['common']['config']['poly'][poly_ind]['l05'],
                    'h': self.signal['common']['config']['poly'][poly_ind]['h'],
                    'stray': {}
                }
                for wl in result.keys():
                    entry['stray'][wl] = []
                    for ch_ind in range(5):
                        if result[wl][poly_ind][ch_ind]['count'] != 0:
                            entry['stray'][wl].append(result[wl][poly_ind][ch_ind]['stray'] /
                                                      result[wl][poly_ind][ch_ind]['count'])
                        else:
                            entry['stray'][wl].append(0)
                self.result['polys'].append(entry)

    def process_shot(self):
        self.result = {
            'timestamp': datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            'spectral_name': self.expected_id,
            'spectral_mod': datetime.fromtimestamp(self.expected['1064']['modification']).strftime('%Y.%m.%d %H:%M:%S'),
            'absolute_name': self.absolute_id,
            'absolute_mod': datetime.fromtimestamp(self.absolute['modification']).strftime('%Y.%m.%d %H:%M:%S'),
            'signal_mod': datetime.fromtimestamp(
                os.path.getmtime('%s%s%05d%s' % (self.db_path, self.SIGNAL_FOLDER, self.shotn, self.FILE_EXT))).
                strftime('%Y.%m.%d %H:%M:%S'),
            'config_name': self.signal['common']['config_name'],
            'polys': []
        }
        print('Processing shot...')

        self.calc_stray()
        self.result['events'] = []

        for event_ind in range(len(self.signal['data'])):
            if 'sync' in self.signal['data'][event_ind] and self.signal['data'][event_ind]['sync']:
                self.result['events'].append(self.signal['data'][event_ind])
                continue
            if 'error' in self.signal['data'][event_ind] and self.signal['data'][event_ind]['error'] != '':
                self.result['events'].append({
                    'error': self.signal['data'][event_ind]['error']
                })
                continue

            proc_event = {
                'timestamp': self.signal['data'][event_ind]['timestamp'],
                'ts': {}
            }
            for wl in self.signal['data'][event_ind]['ts']:
                if wl == '1064':
                    energy = self.expected[wl]['J_from_int'] * self.signal['data'][event_ind]['laser']['ave']['int']
                elif wl == '1047':
                    energy = self.expected[wl]['J_from_int'] * self.signal['data'][event_ind]['laser']['ave']['int_47']
                else:
                    fuck
                proc_event['ts'][wl] = {
                    'energy': energy,
                    'poly': []
                }

                for poly_ind in range(len(self.signal['data'][event_ind]['ts'][wl])):
                    temp = self.calc_temp(self.signal['data'][event_ind]['ts'][wl][poly_ind], poly_ind,
                                          self.result['polys'][poly_ind]['stray'][wl], energy, wl)
                    proc_event['ts'][wl]['poly'].append(temp)
            self.result['events'].append(proc_event)
        self.save_result()

    def save_result(self):
        result_folder = '%s%s%05d/' % (self.db_path, self.RESULT_FOLDER, self.shotn)
        if not os.path.isdir(result_folder):
            os.mkdir(result_folder)
        with open('%s%05d%s' % (result_folder, self.shotn, self.FILE_EXT), 'w') as out_file:
            json.dump(self.result, out_file)
        #self.to_csv()

    def calc_temp(self, event, poly, stray, E, wl):
        channels = []

        E *= self.absolute['E_mult']

        for ch_ind in range(5):
            if event[ch_ind]['error'] is None:
                channels.append(ch_ind)
            else:
                print('Warning! skipped ch%d' % ch_ind)
        if len(channels) > 1:
            chi2 = float('inf')
            N_i = []
            sigm2_i = []

            for ch in channels:
                N_i.append(event[ch]['ph_el'])
                if stray[ch] > 100:
                    N_i[-1] -= stray[ch]
                sigm2_i.append(math.pow(event[ch]['err'], 2))
            min_index = -1
            for i in range(len(self.expected[wl]['T_arr'])):
                f_i = [self.expected[wl]['poly'][poly]['expected'][ch][i] for ch in channels]
                current_chi = calc_chi2(N_i, sigm2_i, f_i)
                if current_chi < chi2:
                    min_index = i
                    chi2 = current_chi
            if min_index >= len(self.expected[wl]['T_arr']) - 2 or min_index == 0:
                res = {
                    'error': 'minimized on edge'
                }
            else:
                left = {
                    't': self.expected[wl]['T_arr'][min_index - 1],
                    'f': [self.expected[wl]['poly'][poly]['expected'][ch][min_index - 1] for ch in channels]
                }
                left['chi'] = calc_chi2(N_i, sigm2_i, left['f'])

                right = {
                    't': self.expected[wl]['T_arr'][min_index + 1],
                    'f': [self.expected[wl]['poly'][poly]['expected'][ch][min_index + 1] for ch in channels]
                }
                right['chi'] = calc_chi2(N_i, sigm2_i, right['f'])

                sec = 1.618

                ml = {
                    't': right['t'] - (right['t'] - left['t']) / sec,
                }
                ml['f'] = [interpolate(left['t'], ml['t'], right['t'], left['f'][ch], right['f'][ch])
                           for ch in range(len(channels))]
                ml['chi'] = calc_chi2(N_i, sigm2_i, ml['f'])

                mr = {
                    't': left['t'] + (right['t'] - left['t']) / sec,
                }
                mr['f'] = [interpolate(left['t'], mr['t'], right['t'], left['f'][ch], right['f'][ch])
                           for ch in range(len(channels))]
                mr['chi'] = calc_chi2(N_i, sigm2_i, mr['f'])
                while right['t'] - left['t'] > 0.05 * left['t']:
                    if ml['chi'] <= mr['chi']:
                        right = mr
                        mr = ml
                        ml = {
                            't': right['t'] - (right['t'] - left['t']) / sec,
                        }
                        ml['f'] = [interpolate(left['t'], ml['t'], right['t'], left['f'][ch], right['f'][ch])
                                   for ch in range(len(channels))]
                        ml['chi'] = calc_chi2(N_i, sigm2_i, ml['f'])
                    else:
                        left = ml
                        ml = mr
                        mr = {
                            't': left['t'] + (right['t'] - left['t']) / sec,
                        }
                        mr['f'] = [interpolate(left['t'], mr['t'], right['t'], left['f'][ch], right['f'][ch])
                                   for ch in range(len(channels))]
                        mr['chi'] = calc_chi2(N_i, sigm2_i, mr['f'])
                f = [(left['f'][ch] + right['f'][ch]) * 0.5 for ch in range(len(channels))]
                df = [(left['f'][ch] - right['f'][ch]) / (left['t'] - right['t']) for ch in range(len(channels))]

                f2_sum = 0
                df_sum = 0
                fdf_sum = 0
                nf_sum = 0
                for ch in range(len(channels)):
                    f2_sum += math.pow(f[ch], 2) / sigm2_i[ch]
                    df_sum += math.pow(df[ch], 2) / sigm2_i[ch]
                    fdf_sum += f[ch] * df[ch] / sigm2_i[ch]
                    nf_sum += N_i[ch] * f[ch] / sigm2_i[ch]
                fdf_sum = math.pow(fdf_sum, 2)

                A = self.absolute['A']['%d' % poly] * self.cross_section

                n_e = nf_sum / (A * E * f2_sum)
                #print('%.2e, %.2e, %.2f' % (A, n_e, E))

                mult = nf_sum / f2_sum

                Terr2 = math.pow(A * E * n_e, -2) * f2_sum / (f2_sum * df_sum - fdf_sum)
                nerr2 = math.pow(A * E, -2) * df_sum / (f2_sum * df_sum - fdf_sum)

                res = self.filter({
                    'index': min_index,
                    'min': self.expected[wl]['T_arr'][min_index],
                    'ch': channels,
                    'chi2': (left['chi'] + right['chi']) * 0.5,
                    'T': (left['t'] + right['t']) * 0.5,
                    'Terr': math.sqrt(Terr2),
                    'n': n_e,
                    'n_err': math.sqrt(nerr2),
                    'mult': mult,
                    'error': None
                })
        else:
            print('Less than 2 signals!')
            res = {
                'error': '< 2 channels'
            }
        return res

    def filter(self, res):
        if res['Terr'] / res['T'] > 0.3:
            res['error'] = 'high Te error'
        elif res['n_err'] / res['n'] > 0.1:
            res['error'] = 'high ne error'
        elif res['chi2'] > 20:
            #res['error'] = 'high chi'
            print('Warning! chi2 filter disabled!')
        return res
