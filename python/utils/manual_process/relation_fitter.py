import os
import json
import ijson
import math

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
    EXPECTED_FOLDER = 'calibration/expected/'
    FILE_EXT = '.json'

    def __init__(self, expected_id, global_db, expected_aux):
        self.expected_id = expected_id
        self.error = None
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

        if len(self.expected['1064']['T_arr']) != len(self.expected['1047']['T_arr']):
            fuck
        if len(self.expected['1064']['poly']) != len(self.expected['1047']['poly']):
            fuck
        self.expected['T_arr'] = self.expected['1064']['T_arr']
        self.expected['rel'] = []
        for poly_ind in range(len(self.expected['1064']['poly'])):
            self.expected['rel'].append([[] for ch in range(5)])
            for t_ind in range(len(self.expected['1064']['T_arr'])):
                for ch in range(5):
                    if self.expected['1047']['poly'][poly_ind]['expected'][ch][t_ind] > 0:
                        val = self.expected['1064']['poly'][poly_ind]['expected'][ch][t_ind] /\
                              self.expected['1047']['poly'][poly_ind]['expected'][ch][t_ind]
                    else:
                        val = 1e123
                    self.expected['rel'][poly_ind][ch].append(val)

        self.result = {}

    def calc_temp(self, relations, poly):
        channels = []
        sec = 1.618

        for ch_ind in range(5):
            if 'skip' not in relations[ch_ind]:
                channels.append(ch_ind)
        if len(channels) > 1:
            chi2 = float('inf')
            N_i = []
            sigm2_i = []

            for ch in channels:
                N_i.append(relations[ch]['val'])
                sigm2_i.append(math.pow(relations[ch]['err'], 2))
            min_index = -1
            for i in range(len(self.expected['T_arr'])):
                f_i = [self.expected['rel'][poly][ch][i] for ch in channels]
                current_chi = calc_chi2(N_i, sigm2_i, f_i)
                if current_chi < chi2:
                    min_index = i
                    chi2 = current_chi
            if min_index >= len(self.expected['T_arr']) - 2 or min_index == 0:
                res = {
                    'error': 'minimized on edge, index = %d' % min_index
                }
            else:
                left = {
                    't': self.expected['T_arr'][min_index - 1],
                    'f': [self.expected['rel'][poly][ch][min_index - 1] for ch in channels]
                }
                left['chi'] = calc_chi2(N_i, sigm2_i, left['f'])

                right = {
                    't': self.expected['T_arr'][min_index + 1],
                    'f': [self.expected['rel'][poly][ch][min_index + 1] for ch in channels]
                }
                right['chi'] = calc_chi2(N_i, sigm2_i, right['f'])

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

                gamma = nf_sum / f2_sum

                Terr2 = math.pow(gamma, -2) * f2_sum / (f2_sum * df_sum - fdf_sum)
                gerr2 = df_sum / (f2_sum * df_sum - fdf_sum)

                res = {
                    'index': min_index,
                    'min': self.expected['T_arr'][min_index],
                    'chi2': (left['chi'] + right['chi']) * 0.5,
                    'T': (left['t'] + right['t']) * 0.5,
                    'Terr': math.sqrt(Terr2),
                    'gamma': gamma,
                    'g_err': math.sqrt(gerr2)
                }
        else:
            print('Less than 2 signals!')
            res = {
                'error': '< 2 channels'
            }
        return res
