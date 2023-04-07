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


def filter(res):
    #if res['Terr'] / res['T'] > 0.3:
    if res['Terr'] / res['T'] > 0.8:
        res['error'] = 'high Te error'
    #elif res['n_err'] / res['n'] > 0.1:
    elif res['n_err'] / res['n'] > 0.4:
        res['error'] = 'high ne error'
    #elif res['chi2'] > 20:
    elif res['chi2'] > 40:
        res['error'] = 'high chi'
    return res


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

    def __init__(self, db_path, shotn, is_plasma, expected_id, absolute_id):
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
        if not os.path.isdir('%s%s' % (self.db_path, self.EXPECTED_FOLDER)):
            self.error = 'Spectral calibration path not found.'
            print(self.error)
            return
        expected_full_name = '%s%s%s%s' % (self.db_path, self.EXPECTED_FOLDER, self.expected_id, self.FILE_EXT)
        if not os.path.isfile(expected_full_name):
            self.error = 'Calibration file not found.'
            print(self.error)
            return
        self.expected = {}
        with open(expected_full_name, 'r') as expected_file:
            obj = ijson.kvitems(expected_file, '', use_float=True)
            for k, v in obj:
                self.expected[k] = v
        self.expected['modification'] = os.path.getmtime(expected_full_name)

        if not os.path.isdir('%s%s' % (self.db_path, self.ABSOLUTE_FOLDER)):
            self.error = 'Spectral calibration path not found.'
            print(self.error)
            return
        absolute_full_name = '%s%s%s%s' % (self.db_path, self.ABSOLUTE_FOLDER, self.absolute_id, self.FILE_EXT)
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

        if self.is_plasma:
            self.prefix = '%s%s' % (self.db_path, self.PLASMA_FOLDER)
        else:
            self.prefix = '%s%s' % (self.db_path, self.DEBUG_FOLDER)
        self.signal = {}
        self.result = {}
        self.load()

    def version_control(self):
        if 'type version' not in self.result['config']:
            return self.result
        res = self.result.copy()
        if res['config']['type version'] >= 1:
            for poly in res['config']['poly']:
                poly['R'] = res['config']['fibers'][poly['fiber']]['R']
                poly['l05'] = res['config']['fibers'][poly['fiber']]['poloidal_length'] * 0.5
                if res['config']['sockets'][res['config']['fibers'][poly['fiber']]['lens_socket']]['image_h'] == 'ceramooptec_half':
                    poly['l05'] *= 0.5
                poly['h'] = res['config']['sockets'][res['config']['fibers'][poly['fiber']]['lens_socket']]['image_h']
        return res

    def get_data(self):
        err = self.get_error()
        if err is None:
            return self.version_control()
        else:
            return {
                'error': err
            }

    def update_events(self, events):
        if len(self.result['events']) != len(events):
            self.error = "New events have different length"
            return False
        self.result['events'] = events
        self.save_result()
        return True

    def get_error(self):
        tmp = self.error
        self.error = None
        return tmp

    def load(self):
        self.result = {}
        result_path = '%s%s%05d/%05d%s' % (self.prefix, self.RESULT_FOLDER, self.shotn, self.shotn, self.FILE_EXT)
        if False and os.path.isfile(result_path):
            print('Loading existing processed result.')
            with open(result_path, 'rb') as signal_file:
                obj = ijson.kvitems(signal_file, '', use_float=True)
                for key, val in obj:
                    if key == 'spectral_name' and val != self.expected_id:
                        print('Warning! existing result was obtained for different spectral calibration! Recalculating...')
                        break
                    if key == 'spectral_mod' and \
                            val != datetime.fromtimestamp(self.expected['modification']).strftime('%Y.%m.%d %H:%M:%S'):
                        print('Warning! Existing result uses outdated spectral calibration! Recalculating...')
                        break

                    if key == 'absolute_name' and val != self.absolute_id:
                        print('Warning! existing result was obtained for different absolute calibration! Recalculating...')
                        break
                    if key == 'absolute_mod' and \
                            val != datetime.fromtimestamp(self.absolute['modification']).strftime('%Y.%m.%d %H:%M:%S'):
                        print('Warning! Existing result uses outdated absolute calibration! Recalculating...')
                        break
                    self.result[key] = val
                else:
                    return
        self.load_signal()
        if self.error is None:
            self.process_shot()

    def load_signal(self):
        print('loading signal...')
        signal_path = '%s%s%05d%s' % (self.prefix, self.SIGNAL_FOLDER, self.shotn, self.FILE_EXT)
        if not os.path.isfile(signal_path):
            self.error = 'No signal file.'
            return
        with open(signal_path, 'r') as signal_file:
            obj = ijson.kvitems(signal_file, '', use_float=True)
            for k, v in obj:
                self.signal[k] = v

    def process_shot(self):
        self.result = {
            'timestamp': datetime.now().strftime('%Y.%m.%d %H:%M:%S'),
            'spectral_name': self.expected_id,
            'spectral_mod': datetime.fromtimestamp(self.expected['modification']).strftime('%Y.%m.%d %H:%M:%S'),
            'absolute_name': self.absolute_id,
            'absolute_mod': datetime.fromtimestamp(self.absolute['modification']).strftime('%Y.%m.%d %H:%M:%S'),
            'signal_mod': datetime.fromtimestamp(
                os.path.getmtime('%s%s%05d%s' % (self.prefix, self.SIGNAL_FOLDER, self.shotn, self.FILE_EXT))).
                strftime('%Y.%m.%d %H:%M:%S'),
            'config_name': self.signal['common']['config_name'],
            'config': self.signal['common']['config'],
            'events': []
        }

        print('Processing shot...')

        stray = [
            [0.0 for ch in range(6)] for poly in range(len(self.result['config']['poly']))
        ]
        count = [
            [0 for ch in range(6)] for poly in range(len(self.result['config']['poly']))
        ]
        if len(self.signal['data']) == 0:
            print('No events!')
            return

        for event_index in range(len(self.signal['data'])):
            if 'error' in self.signal['data'][event_index] and self.signal['data'][event_index]['error'] is not None:
                print('woops: %s, event #' % self.signal['data'][event_index]['error'], event_index)
            else:
                if self.signal['data'][event_index]['timestamp'] >= 100:
                    print('stray calculation stopped at index = %d\n\n' % event_index)
                    break
                event = self.signal['data'][event_index]
                if event['error'] is None:
                    for poly_ind in range(len(event['poly'])):
                        for ch_ind in range(len(event['poly']['%d' % poly_ind]['ch'])):
                            if event['poly']['%d' % poly_ind]['ch'][ch_ind]['error'] is not None:
                                continue

                            count[poly_ind][ch_ind] += 1
                            stray[poly_ind][ch_ind] += event['poly']['%d' % poly_ind]['ch'][ch_ind]['ph_el']

        for poly_ind in range(len(stray)):
            for ch_ind in range(len(stray[poly_ind])):
                if count[poly_ind][ch_ind] > 0:
                    stray[poly_ind][ch_ind] /= count[poly_ind][ch_ind]
            self.result['config']['poly'][poly_ind]['stray'] = stray[poly_ind]

        for event_ind in range(len(self.signal['data'])):
            error = None
            if self.signal['data'][event_ind]['error'] is not None:
                error = self.signal['data'][event_ind]['error']
                self.result['events'].append({
                    'error': self.signal['data'][event_ind]['error']
                })
                continue


            poly = []
            if 'type version' not in self.result['config'] or self.result['config']['type version'] == 1:
                energy = self.signal['data'][event_ind]['laser']['ave']['int'] * self.absolute['J_from_int']
            else:
                energy = self.result['config']['laser'][0]['E']

            for poly_ind in range(len(self.signal['data'][event_ind]['poly'])):
                temp = self.calc_temp(self.signal['data'][event_ind]['poly']['%d' % poly_ind], poly_ind,
                                      stray[poly_ind], energy, event_ind)
                poly.append(temp)
            proc_event = {
                'timestamp': self.signal['data'][event_ind]['timestamp'],
                'energy': energy,
                'T_e': poly,
                'error': error
            }
            self.result['events'].append(proc_event)
        self.save_result()

    def save_result(self):
        result_folder = '%s%s%05d/' % (self.prefix, self.RESULT_FOLDER, self.shotn)
        if not os.path.isdir(result_folder):
            os.mkdir(result_folder)
        with open('%s%05d%s' % (result_folder, self.shotn, self.FILE_EXT), 'w') as out_file:
            json.dump(self.result, out_file, indent=1)
        #self.to_csv()

    def calc_temp(self, event, poly, stray, E, event_ind):
        channels = []

        #E *= self.absolute['E_mult']

        for ch_ind in range(len(self.expected['poly'][poly]['expected'])):
            if event['ch'][ch_ind]['error'] is None:
                channels.append(ch_ind)
            else:
                if event['ch'][ch_ind]['error'] != 'skip':
                    pass
                    #print('Warning! skipped ch%d' % ch_ind)
        if len(channels) > 1:
            chi2 = float('inf')
            N_i = []
            sigm2_i = []

            for ch in channels:
                N_i.append(event['ch'][ch]['ph_el'])
                if stray[ch] > 100:
                    N_i[-1] -= stray[ch]
                sigm2_i.append(math.pow(event['ch'][ch]['err'], 2))
            min_index = -1
            for i in range(len(self.expected['T_arr'])):
                f_i = [self.expected['poly'][poly]['expected'][ch][i] for ch in channels]
                current_chi = calc_chi2(N_i, sigm2_i, f_i)
                if current_chi < chi2:
                    min_index = i
                    chi2 = current_chi
            if min_index >= len(self.expected['T_arr']) - 2 or min_index == 0:
                res = {
                    'error': 'minimized on edge'
                }
            else:
                left = {
                    't': self.expected['T_arr'][min_index - 1],
                    'f': [self.expected['poly'][poly]['expected'][ch][min_index - 1] for ch in channels]
                }
                left['chi'] = calc_chi2(N_i, sigm2_i, left['f'])

                right = {
                    't': self.expected['T_arr'][min_index + 1],
                    'f': [self.expected['poly'][poly]['expected'][ch][min_index + 1] for ch in channels]
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
                    #if poly == 5 and event_ind == 60:
                    #    print('N_i %.1e, f %.1e, sigma2 %.1e' % (N_i[ch], f[ch], sigm2_i[ch]))
                    f2_sum += math.pow(f[ch], 2) / sigm2_i[ch]
                    df_sum += math.pow(df[ch], 2) / sigm2_i[ch]
                    fdf_sum += f[ch] * df[ch] / sigm2_i[ch]
                    nf_sum += N_i[ch] * f[ch] / sigm2_i[ch]
                fdf_sum = math.pow(fdf_sum, 2)

                A = self.absolute['A'][poly] * self.cross_section

                n_e = nf_sum / (A * E * f2_sum)
                #if poly == 5 and event_ind == 60:
                #    print('n_e %.1e, nf_sum %.1e, A %.1e, sigma_TS %.1e, E %.1e, f2_sum %.1e' % (n_e, nf_sum, self.absolute['A'][poly], self.cross_section, E, f2_sum))


                mult = nf_sum / f2_sum
                Terr2 = math.pow(A * E * n_e, -2) * f2_sum / (f2_sum * df_sum - fdf_sum)
                nerr2 = math.pow(A * E, -2) * df_sum / (f2_sum * df_sum - fdf_sum)


                res = filter({
                    'index': min_index,
                    'min': self.expected['T_arr'][min_index],
                    'ch': channels,
                    'chi2': (left['chi'] + right['chi']) * 0.5,
                    'T': (left['t'] + right['t']) * 0.5,
                    'Terr': math.sqrt(Terr2),
                    'n': n_e,
                    'n_err': math.sqrt(nerr2),
                    'mult': mult,
                    'error': None
                })

                if res['error'] == 'high chi':
                    print('Warning, chi2 filter disabled, but triggered for event %d, poly = %d' % (event_ind, poly))
                    res['error'] = None
        else:
            print('Less than 2 signals!')
            res = {
                'error': '< 2 channels'
            }
        return res
