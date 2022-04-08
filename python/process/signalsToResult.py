from datetime import datetime
import os
import ijson
import json
import math
import phys_const as const
import shtRipper

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

    def get_data(self):
        err = self.get_error()
        if err is None:
            return self.result
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
            'config_name': self.signal['common']['config_name'],
            'config': self.signal['common']['config'],
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
                self.result['events'].append({
                    'error': self.signal['data'][event_ind]['error']
                })
                continue
            proc_event = {
                'timestamp': self.signal['data'][event_ind]['timestamp'],
                'energy': self.signal['data'][event_ind]['laser']['ave']['int'] * self.absolute['J_from_int']
            }
            if self.signal['data'][event_ind]['error'] is not None:
                error = self.signal['data'][event_ind]['error']
            else:
                poly = []
                energy = self.signal['data'][event_ind]['laser']['ave']['int'] * self.absolute['J_from_int']

                for poly_ind in range(len(self.signal['data'][event_ind]['poly'])):
                    temp = self.calc_temp(self.signal['data'][event_ind]['poly']['%d' % poly_ind], poly_ind,
                                          stray[poly_ind], energy, event_ind)
                    poly.append(temp)
                proc_event['T_e'] = poly
            proc_event['error'] = error
            self.result['events'].append(proc_event)
        self.save_result()

    def save_result(self):
        result_folder = '%s%s%05d/' % (self.prefix, self.RESULT_FOLDER, self.shotn)
        if not os.path.isdir(result_folder):
            os.mkdir(result_folder)
        with open('%s%05d%s' % (result_folder, self.shotn, self.FILE_EXT), 'w') as out_file:
            json.dump(self.result, out_file)
        #self.to_csv()

    def calc_temp(self, event, poly, stray, E, event_ind):
        channels = []

        #E *= self.absolute['E_mult']

        for ch_ind in range(5):
            if event['ch'][ch_ind]['error'] is None:
                channels.append(ch_ind)
            else:
                if event['ch'][ch_ind]['error'] != 'skip':
                    print('Warning! skipped ch%d' % ch_ind)
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
                    f2_sum += math.pow(f[ch], 2) / sigm2_i[ch]
                    df_sum += math.pow(df[ch], 2) / sigm2_i[ch]
                    fdf_sum += f[ch] * df[ch] / sigm2_i[ch]
                    nf_sum += N_i[ch] * f[ch] / sigm2_i[ch]
                fdf_sum = math.pow(fdf_sum, 2)

                A = self.absolute['A'][poly] * self.cross_section

                n_e = nf_sum / (A * E * f2_sum)
                #print('%.2e, %.2e, %.2f' % (A, n_e, E))

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

    def dump_dynamics(self, correction: float, data, x_from: float, x_to:float):
        to_pack = {}
        aux = ''
        if data is not None:
            timestamps = []
            nl42 = []
            nl42_err = []
            # расстояние до сепаратрисы
            # температура и концентрация на сепаратрисе
            # градиент на сепаратрисе
            nl_ave = []
            nl_ave_err = []
            n_ave = []
            n_ave_err = []
            t_ave = []
            t_ave_err = []
            we = []
            we_err = []
            dwe = []
            vol = []
            t_c = []
            t_c_err = []
            n_c = []
            n_c_err = []
            t_p = []
            n_p = []
            r_sep_arr = []
            cfm_timestamps = []
            nl_eq = []
            nl_eq_err = []
            eq_length = []
            nl_eq_ave = []
            nl_eq_ave_err = []

            aux += 'index, time, nl42, nl42_err, l42, <n>42, <n>42_err, <n>V, <n>V_err, <T>V, <T>V_err, We, We_err, dWe/dt, vol, T_center, T_c_err, n_center, n_c_err, T_peaking, n_peaking, R_sep, nl_eq, nl_eq_err, len_eq, <n>eq, <n>eq_err\n'
            aux += '1, ms, m-2, m-2, m, m-3, m-3, m-3, m-3, eV, eV, J, J, kW, m3, eV, eV, m-3, m-3, 1, 1, cm, m-2, m-2, m, m-3, m-3\n'
            for event_ind_aux in range(len(data)):
                event = data[event_ind_aux]

                event_ind = event['event_index']
                if 'error' in event:
                    continue
                if x_from <= self.result['events'][event_ind]['timestamp'] <= x_to:
                    if 'error' not in event['data'] and len(event['data']['nl_profile']) != 0:
                        length = (event['data']['nl_profile'][0]['z'] - event['data']['nl_profile'][-1]['z']) * 1e-2
                        length_eq = math.sqrt(math.pow((event['data']['surfaces'][0]['r_max']), 2) - (17 * 17)) * 2 * 1e-2
                        eq_length.append(length_eq)
                        we_derivative = 0
                        if len(data) > 1:
                            if 'error' in data[event_ind_aux]:
                                we_derivative = 0
                            elif event_ind_aux == 0:
                                if 'error' not in data[event_ind_aux + 1]:
                                    we_derivative = (data[event_ind_aux + 1]['data']['vol_w'] - event['data'][
                                        'vol_w']) * correction / (self.result['events'][
                                                                      data[event_ind_aux + 1]['event_index']]['timestamp'] -
                                                                  self.result['events'][event_ind]['timestamp'])
                            elif event_ind_aux == len(data) - 1:
                                if 'error' not in data[event_ind_aux - 1]:
                                    we_derivative = (data[event_ind_aux - 1]['data']['vol_w'] - event['data'][
                                        'vol_w']) * correction / (self.result['events'][
                                                                      data[event_ind_aux - 1]['event_index']]['timestamp'] -
                                                                  self.result['events'][event_ind]['timestamp'])

                            elif len(data) > 2 and 'error' not in data[event_ind_aux - 1] and 'error' not in data[event_ind_aux + 1]:
                                we_derivative = (data[event_ind_aux + 1]['data']['vol_w'] -
                                                 data[event_ind_aux - 1]['data']['vol_w']) * correction / \
                                                (self.result['events'][data[event_ind_aux + 1]['event_index']][
                                                     'timestamp'] -
                                                 self.result['events'][data[event_ind_aux - 1]['event_index']][
                                                     'timestamp'])

                        timestamps.append(self.result['events'][event_ind]['timestamp'] * 1e-3)
                        nl42.append(event['data']['nl'] * correction)
                        nl42_err.append(event['data']['nl_err'] * correction)

                        nl_ave.append(event['data']['nl'] * correction / length)
                        nl_ave_err.append(event['data']['nl_err'] * correction / length)

                        n_ave.append(event['data']['n_vol'] * correction)
                        n_ave_err.append(event['data']['n_vol_err'] * correction)

                        t_ave.append(event['data']['t_vol'])
                        t_ave_err.append(event['data']['t_vol_err'])

                        we.append(event['data']['vol_w'] * correction)
                        we_err.append(event['data']['w_err'] * correction)

                        dwe.append(we_derivative)
                        vol.append(event['data']['vol'])

                        t_c.append(event['data']['surfaces'][-1]['Te'])
                        t_c_err.append(event['data']['surfaces'][-1]['Te_err'])

                        n_c.append(event['data']['surfaces'][-1]['ne'] * correction)
                        n_c_err.append(event['data']['surfaces'][-1]['ne_err'] * correction)

                        t_p.append(event['data']['surfaces'][-1]['Te'] / event['data']['t_vol'])
                        n_p.append(event['data']['surfaces'][-1]['ne'] / event['data']['n_vol'])

                        nl_eq.append(event['data']['nl_eq'] * correction)
                        nl_eq_err.append(event['data']['nl_eq_err'] * correction)

                        nl_eq_ave.append(event['data']['nl_eq'] * correction / length_eq)
                        nl_eq_ave_err.append(event['data']['nl_eq_err'] * correction / length_eq)

                        surf = event['data']['surfaces'][0]
                        for surf_ind in range(len(surf['z']) - 1):
                            if surf['z'][surf_ind] >= 0 > surf['z'][surf_ind + 1] and surf['r'][surf_ind] > 40:
                                r_sep_val = surf['r'][surf_ind]
                                r_sep_arr.append(r_sep_val)
                                cfm_timestamps.append(timestamps[-1])
                                break
                            else:
                                r_sep_val = -1


                        aux += '%d, %.1f, %.2e, %.2e, %.2f, %.2e, %.2e, %.2e, %.2e, %.2f, %.2f, %d, %d, %d, %.3f, %.2f, %.2f, %.2e, %.2e, %.3f, %.3f, %.2f, %.2e, %.2e, %.2f, %.2e, %.2e\n' % \
                               (event_ind, self.result['events'][event_ind]['timestamp'],
                                event['data']['nl'] * correction, event['data']['nl_err'] * correction,
                                length,
                                event['data']['nl'] * correction / length, event['data']['nl_err'] * correction / length,
                                event['data']['n_vol'] * correction, event['data']['n_vol_err'] * correction,
                                event['data']['t_vol'], event['data']['t_vol_err'],
                                event['data']['vol_w'] * correction, event['data']['w_err'] * correction, we_derivative,
                                event['data']['vol'],
                                event['data']['surfaces'][-1]['Te'], event['data']['surfaces'][-1]['Te_err'],
                                event['data']['surfaces'][-1]['ne'] * correction,
                                event['data']['surfaces'][-1]['ne_err'] * correction,
                                event['data']['surfaces'][-1]['Te'] / event['data']['t_vol'],
                                event['data']['surfaces'][-1]['ne'] / event['data']['n_vol'],
                                r_sep_val,
                                event['data']['nl_eq'] * correction, event['data']['nl_eq_err'] * correction,
                                length_eq,
                                event['data']['nl_eq'] * correction / length_eq, event['data']['nl_eq_err'] * correction / length_eq
                        )
                    else:
                        aux += '%d, %.1f, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --\n' % \
                               (event_ind, self.result['events'][event_ind]['timestamp'])
            to_pack = {
                'nl42 (m^-2)': {
                    'comment': 'линейная концентрация по хорде R=42',
                    'unit': 'nl42(m^-2)',
                    'x': timestamps,
                    'y': nl42,
                    'err': nl42_err
                },
                'nl_eq (m^-2)': {
                    'comment': 'линейная концентрация по экваториальной хорде',
                    'unit': 'nl_eq(m^-2)',
                    'x': timestamps,
                    'y': nl_eq,
                    'err': nl_eq_err
                },
                '<nl42> (m^-3)': {
                    'comment': 'средняя концентрация по хорде R=42',
                    'unit': '<nl42>(m^-3)',
                    'x': timestamps,
                    'y': nl_ave,
                    'err': nl_ave_err
                },
                '<nl_eq> (m^-3)': {
                    'comment': 'средняя концентрация по экваториальной хорде',
                    'unit': '<nl_eq>(m^-3)',
                    'x': timestamps,
                    'y': nl_eq_ave,
                    'err': nl_eq_ave_err
                },
                '<ne> (m^-3)': {
                    'comment': 'средняя по объёму концентрация',
                    'unit': '<n>(m^-3)',
                    'x': timestamps,
                    'y': n_ave,
                    'err': n_ave_err
                },
                '<Te>': {
                    'comment': 'средняя по объёму температура',
                    'unit': '<Te>(eV)',
                    'x': timestamps,
                    'y': t_ave,
                    'err': t_ave_err
                },
                'We': {
                    'comment': 'энергозапас в электронном компоненте',
                    'unit': 'We(J)',
                    'x': timestamps,
                    'y': we,
                    'err': we_err
                },
                'dWe/dt': {
                    'comment': 'производная энергозапаса в электронном компоненте',
                    'unit': 'dWe/dt(kW)',
                    'x': timestamps,
                    'y': dwe
                },
                'plasma volume': {
                    'comment': 'объём плазмы внутри сепаратрисы',
                    'unit': 'V(m^-3)',
                    'x': timestamps,
                    'y': vol
                },
                'Te central': {
                    'comment': 'температура в ближайшей к центру точке',
                    'unit': 'Te(eV)',
                    'x': timestamps,
                    'y': t_c,
                    'err': t_c_err
                },
                'ne central (m^-3)': {
                    'comment': 'концентрация в ближайшей к центру точке',
                    'unit': 'ne(m^-3)',
                    'x': timestamps,
                    'y': n_c,
                    'err': n_c_err
                },
                'Te peaking': {
                    'comment': 'мера пикированности профиля температуры = (Te central) / <Te>',
                    'unit': 'пикированность(1)',
                    'x': timestamps,
                    'y': t_p
                },
                'ne peaking': {
                    'comment': 'мера пикированности профиля концентрации = (ne central) / <ne>',
                    'unit': 'пикированность(1)',
                    'x': timestamps,
                    'y': n_p
                },
                'R_sep положение сепаратрисы': {
                    'comment': 'Большой радиус сепаратрисы в экваториальной плоскости вакуумной камеры на стороне слабого поля',
                    'unit': 'R_sep (cm)',
                    'x': cfm_timestamps,
                    'y': r_sep_arr
                },
                'len_eq (m)': {
                    'comment': 'длина экваториальной хорды',
                    'unit': 'l_eq(m)',
                    'x': timestamps,
                    'y': eq_length
                },
            }

        serialised = [{
            'x': [],
            't': [],
            'te': [],
            'n': [],
            'ne': []
        } for poly in self.result['config']['poly']]

        for event_ind in range(len(self.result['events'])):
            if 'timestamp' in self.result['events'][event_ind]:
                if x_from <= self.result['events'][event_ind]['timestamp'] <= x_to:
                    for poly_ind in range(len(self.result['events'][event_ind]['T_e'])):
                        poly = self.result['events'][event_ind]['T_e'][poly_ind]
                        if poly['error'] is None and not ('hidden' in poly and poly['hidden']):
                            serialised[poly_ind]['x'].append(self.result['events'][event_ind]['timestamp'] * 1e-3)
                            serialised[poly_ind]['t'].append(poly['T'])
                            serialised[poly_ind]['te'].append(poly['Terr'])
                            serialised[poly_ind]['n'].append(poly['n'] * correction)
                            serialised[poly_ind]['ne'].append(poly['n_err'] * correction)
        for poly_ind in range(len(serialised)):
            to_pack['Te R%d' % (self.result['config']['poly'][poly_ind]['R'] / 10)] = {
                    'comment': 'локальная температура электронов',
                    'unit': 'Te(eV)',
                    'x': serialised[poly_ind]['x'],
                    'y': serialised[poly_ind]['t'],
                    'err': serialised[poly_ind]['te']
                }
            to_pack['ne R%d' % (self.result['config']['poly'][poly_ind]['R'] / 10)] = {
                'comment': 'm^-3, локальная концентрация электронов',
                'unit': 'ne(m^-3)',
                'x': serialised[poly_ind]['x'],
                'y': serialised[poly_ind]['n'],
                'err': serialised[poly_ind]['ne']
            }

        packed = shtRipper.ripper.write(path='%s%s%05d/' % (self.prefix, self.RESULT_FOLDER, self.shotn),
                                        filename='TS_%05d.sht' % self.shotn, data=to_pack)
        if len(packed) != 0:
            print('sht packing error: "%s"' % packed)

        if len(aux) == 0:
            return None
        return aux[:-1]

    def to_csv(self, x_from, x_to, correction, aux_data=None):
        temp_evo = ''
        line = 't, '
        for poly in self.result['config']['poly']:
            line += '%.1f, err, ' % poly['R']
        temp_evo += line[:-2] + '\n'
        line = 'ms, '
        for poly in self.result['config']['poly']:
            line += 'eV, eV, '
        temp_evo += line[:-2] + '\n'
        for event_ind in range(len(self.result['events'])):
            if 'timestamp' in self.result['events'][event_ind]:
                if x_from <= self.result['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.1f, ' % self.result['events'][event_ind]['timestamp']
                    for poly in self.result['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                    temp_evo += line[:-2] + '\n'
        temp_prof = ''
        names = 'R, '
        units = 'mm, '
        for event in self.result['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.1f, err, ' % event['timestamp']
                    units += 'eV, eV, '
        temp_prof += names[:-2] + '\n'
        temp_prof += units[:-2] + '\n'
        for poly_ind in range(len(self.result['config']['poly'])):
            line = '%.1f, ' % self.result['config']['poly'][poly_ind]['R']
            for event in self.result['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.1f, %.1f, ' % (event['T_e'][poly_ind]['T'], event['T_e'][poly_ind]['Terr'])
            temp_prof += line[:-2] + '\n'

        dens_evo = ''
        line = 't, '
        for poly in self.result['config']['poly']:
            line += '%.1f, err, ' % poly['R']
        dens_evo += line[:-2] + '\n'
        line = 'ms, '
        for poly in self.result['config']['poly']:
            line += 'm-3, m-3, '
        dens_evo += line[:-2] + '\n'
        for event_ind in range(len(self.result['events'])):
            if 'timestamp' in self.result['events'][event_ind]:
                if x_from <= self.result['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.1f, ' % self.result['events'][event_ind]['timestamp']
                    for poly in self.result['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.2e, %.2e, ' % (poly['n'] * correction, poly['n_err'] * correction)
                    dens_evo += line[:-2] + '\n'

        dens_prof = ''
        names = 'R, '
        units = 'mm, '
        for event in self.result['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.1f, err, ' % event['timestamp']
                    units += 'm-3, m-3, '
        dens_prof += names[:-2] + '\n'
        dens_prof += units[:-2] + '\n'
        for poly_ind in range(len(self.result['config']['poly'])):
            line = '%.1f, ' % self.result['config']['poly'][poly_ind]['R']
            for event in self.result['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.2e, %.2e, ' % (event['T_e'][poly_ind]['n'] * correction,
                                                      event['T_e'][poly_ind]['n_err'] * correction)
            dens_prof += line[:-2] + '\n'

        dynamics = self.dump_dynamics(correction, aux_data, x_from, x_to)
        return {
            'ok': True,
            'Tt': temp_evo,
            'TR': temp_prof,
            'nt': dens_evo,
            'nR': dens_prof,
            'aux': dynamics
        }

    def to_old_csv(self, x_from, x_to, correction, aux_data=None):
        temp_evo = ''
        line = 't, '
        for poly in self.result['config']['poly']:
            line += '%.4fcm, %.4fcm, ' % (poly['R'] * 1e-3, poly['R'] * 1e-3)
        temp_evo += line[:-2] + '\n'
        for event_ind in range(len(self.result['events'])):
            if 'timestamp' in self.result['events'][event_ind]:
                if x_from <= self.result['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.4f, ' % (self.result['events'][event_ind]['timestamp'] * 1e-3)
                    for poly in self.result['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                    temp_evo += line[:-2] + '\n'
        temp_prof = ''
        names = 'R, '
        for event in self.result['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.4fs, %.4fs, ' % (event['timestamp'] * 1e-3, event['timestamp'] * 1e-3)
        temp_prof += names[:-2] + '\n'
        for poly_ind in range(len(self.result['config']['poly'])):
            line = '%.4f, ' % (self.result['config']['poly'][poly_ind]['R'] * 1e-3)
            for event in self.result['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.1f, %.1f, ' % (event['T_e'][poly_ind]['T'], event['T_e'][poly_ind]['Terr'])
            temp_prof += line[:-2] + '\n'

        dens_evo = ''
        line = 't, '
        for poly in self.result['config']['poly']:
            line += '%.4fcm, %.4fcm, ' % (poly['R'] * 1e-3, poly['R'] * 1e-3)
        dens_evo += line[:-2] + '\n'
        for event_ind in range(len(self.result['events'])):
            if 'timestamp' in self.result['events'][event_ind]:
                if x_from <= self.result['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.4f, ' % (self.result['events'][event_ind]['timestamp'] * 1e-3)
                    for poly in self.result['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.2e, %.2e, ' % (poly['n'] * correction * 1e-6, poly['n_err'] * correction  * 1e-6)
                    dens_evo += line[:-2] + '\n'

        dens_prof = ''
        names = 'R, '
        for event in self.result['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.4fs, %.4fs, ' % (event['timestamp'] * 1e-3, event['timestamp'] * 1e-3)
        dens_prof += names[:-2] + '\n'
        for poly_ind in range(len(self.result['config']['poly'])):
            line = '%.4f, ' % (self.result['config']['poly'][poly_ind]['R'] * 1e-3)
            for event in self.result['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.2e, %.2e, ' % (event['T_e'][poly_ind]['n'] * correction * 1e-6,
                                                      event['T_e'][poly_ind]['n_err'] * correction * 1e-6)
            dens_prof += line[:-2] + '\n'

        dynamics = self.dump_dynamics(correction, aux_data, x_from, x_to)
        return {
            'ok': True,
            'Tt': temp_evo,
            'TR': temp_prof,
            'nt': dens_evo,
            'nR': dens_prof,
            'aux': dynamics
        }
