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

    def __init__(self, db_path, shotn, is_plasma, expected_id, absolute_id):
        self.shotn = shotn
        self.is_plasma = is_plasma
        self.expected_id = expected_id
        self.absolute_id = absolute_id
        self.error = None
        if not os.path.isdir(db_path):
            self.error = 'Database path not found.'
            return
        self.db_path = db_path
        if not os.path.isdir('%s%s' % (self.db_path, self.EXPECTED_FOLDER)):
            self.error = 'Spectral calibration path not found.'
            return
        expected_full_name = '%s%s%s%s' % (self.db_path, self.EXPECTED_FOLDER, self.expected_id, self.FILE_EXT)
        if not os.path.isfile(expected_full_name):
            self.error = 'Calibration file not found.'
            return
        self.expected = {}
        with open(expected_full_name, 'r') as expected_file:
            obj = ijson.kvitems(expected_file, '', use_float=True)
            for k, v in obj:
                self.expected[k] = v
        self.expected['modification'] = os.path.getmtime(expected_full_name)

        if not os.path.isdir('%s%s' % (self.db_path, self.ABSOLUTE_FOLDER)):
            self.error = 'Spectral calibration path not found.'
            return
        absolute_full_name = '%s%s%s%s' % (self.db_path, self.ABSOLUTE_FOLDER, self.absolute_id, self.FILE_EXT)
        if not os.path.isfile(absolute_full_name):
            self.error = 'Calibration file not found.'
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

    def get_data(self):
        err = self.get_error()
        if err is None:
            return self.result
        else:
            return {
                'processed_bad': True,
                'error': err
            }


    def get_error(self):
        tmp = self.error
        self.error = None
        return tmp

    def load(self):
        self.result = {}
        result_path = '%s%s%05d/%05d%s' % (self.prefix, self.RESULT_FOLDER, self.shotn, self.shotn, self.FILE_EXT)
        if os.path.isfile(result_path):
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
            'polys': [],
            'events': []
        }
        print('Processing shot...')

        stray = [
            [0.0 for ch in range(5)] for poly in range(10)
        ]
        count = [
            [0 for ch in range(5)] for poly in range(10)
        ]
        if len(self.signal['data']) == 0:
            print('No events!')
            return
        current_index = 0
        while self.signal['data'][current_index]['timestamp'] <= 100:
            event = self.signal['data'][current_index]
            if not event['processed_bad']:
                for poly_ind in range(len(event['poly'])):
                    for ch_ind in range(len(event['poly']['%d' % poly_ind]['ch'])):
                        if event['poly']['%d' % poly_ind]['ch'][ch_ind]['processed_bad']:
                            continue
                        count[poly_ind][ch_ind] += 1
                        stray[poly_ind][ch_ind] += event['poly']['%d' % poly_ind]['ch'][ch_ind]['ph_el']
            current_index += 1
        for poly_ind in range(len(stray)):
            self.result['polys'].append({
                'ind': self.signal['common']['config']['poly'][poly_ind]['ind'],
                'fiber': self.signal['common']['config']['poly'][poly_ind]['fiber'],
                'R': self.signal['common']['config']['poly'][poly_ind]['R'],
                'l05': self.signal['common']['config']['poly'][poly_ind]['l05'],
                'h': self.signal['common']['config']['poly'][poly_ind]['h']
            })
            poly = stray[poly_ind]
            for ch_ind in range(len(poly)):
                poly[ch_ind] /= count[poly_ind][ch_ind]
            # print(poly)

        for event_ind in range(len(self.signal['data'])):
            bad_flag = False
            proc_event = {
                'timestamp': self.signal['data'][event_ind]['timestamp'],
                'energy': self.signal['data'][event_ind]['laser']['ave']['int'] * self.expected['J_from_int']
            }
            if self.signal['data'][event_ind]['processed_bad']:
                bad_flag = True
            else:
                poly = []
                energy = self.expected['J_from_int'] * self.signal['data'][event_ind]['laser']['ave']['int']

                energy = 1  ## DEBUG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                for poly_ind in range(len(self.signal['data'][event_ind]['poly'])):
                    temp = self.calc_temp(self.signal['data'][event_ind]['poly']['%d' % poly_ind], poly_ind,
                                          stray[poly_ind], energy)
                    poly.append(temp)
                proc_event['T_e'] = poly
            proc_event['processed_bad'] = bad_flag
            self.result['events'].append(proc_event)
        result_folder = '%s%s%05d/' % (self.prefix, self.RESULT_FOLDER, self.shotn)
        if not os.path.isdir(result_folder):
            os.mkdir(result_folder)
        with open('%s%05d%s' % (result_folder, self.shotn, self.FILE_EXT), 'w') as out_file:
            json.dump(self.result, out_file)
        self.to_csv(stray)

    def calc_temp(self, event, poly, stray, E):
        channels = []
        for ch_ind in range(5):
            if not event['ch'][ch_ind]['processed_bad']:
                channels.append(ch_ind)
            else:
                print('Warning! skipped ch%d' % ch_ind)
        if len(channels) > 1:
            chi2 = float('inf')
            N_i = []
            sigm2_i = []
            for ch in channels:
                N_i.append(event['ch'][ch]['ph_el'])
                if stray[ch] > 500:
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
                    'processed_bad': True
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
                df = [(left['f'][ch] - right['f'][ch]) / (left['t'] - right['t'])
                      for ch in range(len(channels))]

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

                A = self.absolute['%d' % poly] * self.cross_section

                n_e = nf_sum / (A * E * f2_sum)

                mult = nf_sum / f2_sum

                Terr2 = math.pow(A * E * n_e, -2) * f2_sum / (f2_sum * df_sum - fdf_sum)
                nerr2 = math.pow(A * E, -2) * df_sum / (f2_sum * df_sum - fdf_sum)
                res = {
                    'index': min_index,
                    'min': self.expected['T_arr'][min_index],
                    'ch': channels,
                    'chi2': (left['chi'] + right['chi']) * 0.5,
                    'T': (left['t'] + right['t']) * 0.5,
                    'Terr': math.sqrt(Terr2),
                    'n': n_e,
                    'n_err': math.sqrt(nerr2),
                    'mult': mult,
                    'processed_bad': False
                }
        else:
            print('Less than 2 signals!')
            res = {
                'processed_bad': True
            }
        return res

    def to_csv(self, stray):
        out_folder = '%s%s%05d/' % (self.prefix, self.RESULT_FOLDER, self.shotn)
        with open('%sT(t).csv' % out_folder, 'w') as out_file:
            line = 't, '
            for poly in self.signal['common']['config']['poly']:
                line += '%.1f, err, ' % poly['R']
            out_file.write(line[:-2] + '\n')
            line = 'ms, '
            for poly in self.signal['common']['config']['poly']:
                line += 'eV, eV,'
            out_file.write(line[:-2] + '\n')
            for event_ind in range(len(self.result['events'])):
                line = '%.1f, ' % self.result['events'][event_ind]['timestamp']
                for poly in self.result['events'][event_ind]['T_e']:
                    if poly['processed_bad']:
                        line += '--, --, '
                    else:
                        line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                out_file.write(line[:-2] + '\n')

        with open('%sT(R).csv' % out_folder, 'w') as out_file:
            names = 'R, '
            units = 'mm, '
            for event in self.result['events']:
                names += '%.1f, err, ' % event['timestamp']
                units += 'eV, eV, '
            out_file.write(names[:-2] + '\n')
            out_file.write(units[:-2] + '\n')
            for poly_ind in range(len(self.signal['common']['config']['poly'])):
                line = '%.1f, ' % self.signal['common']['config']['poly'][poly_ind]['R']
                for event in self.result['events']:
                    if event['T_e'][poly_ind]['processed_bad']:
                        line += '--, --, '
                    else:
                        line += '%.1f, %.1f, ' % (event['T_e'][poly_ind]['T'], event['T_e'][poly_ind]['Terr'])
                out_file.write(line[:-2] + '\n')

        with open('%sn(t).csv' % out_folder, 'w') as out_file:
            line = 't, '
            for poly in self.signal['common']['config']['poly']:
                line += '%.1f, err, ' % poly['R']
            out_file.write(line[:-2] + '\n')
            line = 'ms, '
            for poly in self.signal['common']['config']['poly']:
                line += 'a.u., a.u.,'
            out_file.write(line[:-2] + '\n')
            for event_ind in range(len(self.result['events'])):
                line = '%.1f, ' % self.result['events'][event_ind]['timestamp']
                for poly in self.result['events'][event_ind]['T_e']:
                    if poly['processed_bad']:
                        line += '--, --, '
                    else:
                        line += '%.2e, %.2e, ' % (poly['n'], poly['n_err'])
                out_file.write(line[:-2] + '\n')

        with open('%sn(R).csv' % out_folder, 'w') as out_file:
            names = 'R, '
            units = 'mm, '
            for event in self.result['events']:
                names += '%.1f, err, ' % event['timestamp']
                units += 'a.u., a.u., '
            out_file.write(names[:-2] + '\n')
            out_file.write(units[:-2] + '\n')
            for poly_ind in range(len(self.signal['common']['config']['poly'])):
                line = '%.1f, ' % self.signal['common']['config']['poly'][poly_ind]['R']
                for event in self.result['events']:
                    if event['T_e'][poly_ind]['processed_bad']:
                        line += '--, --, '
                    else:
                        line += '%.2e, %.2e, ' % (event['T_e'][poly_ind]['n'], event['T_e'][poly_ind]['n_err'])
                out_file.write(line[:-2] + '\n')

        '''
        with open('%sAux(t).csv' % out_folder, 'w') as out_file:
            names = 't, E, '
            names += 'p0c1, err, p0c2, err, p0c3, err, '
            names += 'p1c1, err, p1c2, err, p1c3, err, '
            names += 'p2c1, err, p2c2, err, p2c3, err, '
            out_file.write(names[:-2] + '\n')

            units = 'ms, mv*ns, '
            units += 'ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., '
            units += 'ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., '
            units += 'ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., '
            out_file.write(units[:-2] + '\n')

            for event in self.signal['data']:
                line = '%.1f, %.2f, ' % (event['timestamp'], event['laser']['ave']['int'])
                for poly_ind in range(3):
                    poly = event['poly']['%d' % poly_ind]
                    for ch in range(3):
                        if poly['ch'][ch]['processed_bad']:
                            line += '--, --, '
                        else:
                            if ch == 0:
                                line += '%.1f, %.1f, ' % (poly['ch'][ch]['ph_el'] - stray[poly_ind][ch],
                                                          poly['ch'][ch]['err'])
                            else:
                                line += '%.1f, %.1f, ' % (poly['ch'][ch]['ph_el'], poly['ch'][ch]['err'])
                out_file.write(line[:-2] + '\n')
        '''
