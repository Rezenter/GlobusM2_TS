import os
import ijson
import json
import math


def calc_chi2(N_i, sigm2_i, f_i):
    res = 0
    top_sum = 0
    bot_sum = 0
    for ch in range(len(N_i)):
        top_sum += (N_i[ch] * f_i[ch]) / sigm2_i[ch]
        bot_sum += math.pow(f_i[ch], 2) / sigm2_i[ch]
    for ch in range(len(N_i)):
        res += math.pow(N_i[ch] - (top_sum * f_i[ch]/ bot_sum), 2) / sigm2_i[ch]
    return res


def interpolate(x1, x, x2, y1, y2):
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


class Processor:
    PLASMA_FOLDER = 'plasma/'
    DEBUG_FOLDER = 'debug/'
    SIGNAL_FOLDER = 'signal/'
    RESULT_FOLDER = 'result/'
    CALIBR_FOLDER = 'calibration/expected/'
    HEADER_FILE = 'header'
    FILE_EXT = '.json'

    def __init__(self, db_path, shotn, is_plasma, calibration):
        self.shotn = shotn
        self.is_plasma = is_plasma
        self.calibration = calibration
        self.error = None
        if not os.path.isdir(db_path):
            self.error = 'Database path not found.'
            return
        self.db_path = db_path
        if not os.path.isdir('%s%s' % (self.db_path, self.CALIBR_FOLDER)):
            self.error = 'Calibration path not found.'
            return
        calibr_full_name = '%s%s%s%s' % (self.db_path, self.CALIBR_FOLDER, self.calibration, self.FILE_EXT)
        if not os.path.isfile(calibr_full_name):
            self.error = 'Calibration file not found.'
            return
        self.calibr = {}
        with open(calibr_full_name, 'r') as config_file:
            obj = ijson.kvitems(config_file, '', use_float=True)
            for k, v in obj:
                self.calibr[k] = v
        if self.is_plasma:
            self.prefix = '%s%s' % (self.db_path, self.PLASMA_FOLDER)
        else:
            self.prefix = '%s%s' % (self.db_path, self.DEBUG_FOLDER)
        self.signal = {}
        self.result = {}
        self.load()

    def get_error(self):
        tmp = self.error
        self.error = None
        return tmp

    def load(self):
        self.result = []
        result_path = '%s%s%05d%s' % (self.prefix, self.RESULT_FOLDER, self.shotn, self.FILE_EXT)
        if os.path.isfile(result_path):
            print('Loading existing processed result.')
            with open(result_path, 'rb') as signal_file:
                obj = ijson.items(signal_file, 'common.config_name', use_float=True)
                for val in obj:
                    if val == self.config_name:
                        signal_file.seek(0)
                        obj = ijson.items(signal_file, 'data.item', use_float=True)
                        for event in obj:
                            self.processed.append(event)
                        return True
        self.load_signal()
        self.process_shot()
        return True

    def load_signal(self):
        print('loading signal...')
        signal_path = '%s%s%05d%s' % (self.prefix, self.SIGNAL_FOLDER, self.shotn, self.FILE_EXT)
        with open(signal_path, 'r') as signal_file:
            obj = ijson.kvitems(signal_file, '', use_float=True)
            for k, v in obj:
                self.signal[k] = v

    def process_shot(self):
        self.result = []
        print('Processing shot...')
        for event_ind in range(len(self.signal['data'])):
            bad_flag = False
            proc_event = {}
            if self.signal['data'][event_ind]['processed_bad']:
                bad_flag = True
            else:
                poly = []
                for poly_ind in range(len(self.signal['data'][event_ind]['poly'])):
                    temp = self.calc_temp(self.signal['data'][event_ind]['poly']['%d' % poly_ind], poly_ind)
                    poly.append(temp)
                proc_event['T_e'] = poly
            proc_event['processed_bad'] = bad_flag
            self.result.append(proc_event)
        with open('out/result.json', 'w') as out_file:
            json.dump(self.result, out_file)
        self.to_csv()

    def calc_temp(self, event, poly):
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
                sigm2_i.append(math.pow(event['ch'][ch]['err'], 2))
            min_index = -1
            for i in range(len(self.calibr['T_arr'])):
                f_i = [self.calibr['poly'][poly]['expected'][ch][i] for ch in channels]
                current_chi = calc_chi2(N_i, sigm2_i, f_i)
                if current_chi < chi2:
                    min_index = i
                    chi2 = current_chi
            if min_index >= len(self.calibr['T_arr']) - 2 or min_index == 0:
                res = {
                    'processed_bad': True
                }
            else:
                left = {
                    't': self.calibr['T_arr'][min_index - 1],
                    'f': [self.calibr['poly'][poly]['expected'][ch][min_index - 1] for ch in channels]
                }
                left['chi'] = calc_chi2(N_i, sigm2_i, left['f'])

                right = {
                    't': self.calibr['T_arr'][min_index + 1],
                    'f': [self.calibr['poly'][poly]['expected'][ch][min_index + 1] for ch in channels]
                }
                right['chi'] = calc_chi2(N_i, sigm2_i, right['f'])

                sec = 1.618

                ml  = {
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
                while right['t'] - left['t'] > 1:
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
                res = {
                    'index': min_index,
                    'min': self.calibr['T_arr'][min_index],
                    'ch': channels,
                    'chi2': (left['chi'] + right['chi']) * 0.5,
                    'T': (left['t'] + right['t']) * 0.5,
                    'processed_bad': False
                }
        else:
            print('Less than 2 signals!')
            res = {
                'processed_bad': True
            }
        return res

    def to_csv(self):
        with open('out/T(t).csv', 'w') as out_file:
            line = ''
            for poly in self.signal['common']['config']['poly']:
                line += '%.1f, ' % poly['R']
            out_file.write(line[:-2] + '\n')
            line = ''
            for poly in self.signal['common']['config']['poly']:
                line += 'mm, '
            out_file.write(line[:-2] + '\n')
            for event in self.result:
                line = ''
                for poly in event['T_e']:
                    if poly['processed_bad']:
                        line += '--, '
                    else:
                        line += '%.1f, ' % poly['T']
                out_file.write(line[:-2] + '\n')
