import os
import ijson
import json
import statistics
import math


def find_front_findex(signal, threshold, rising=True):
    if rising:
        for i in range(len(signal) - 1):
            if signal[i + 1] >= threshold > signal[i]:
                return i + (threshold - signal[i]) / (signal[i + 1] - signal[i])
    else:
        for i in range(len(signal) - 1):
            if signal[i] >= threshold > signal[i + 1]:
                return i + (signal[i] - threshold) / (signal[i] - signal[i + 1])
    return -1


class Integrator:
    extension = '.json'
    config_path = '../configs/'
    db_path = 'd:/data/fastDump/'

    # move to config!
    group_per_board = 8
    ch_per_group = 2
    adc_baseline = 1250
    offscale_threshold = 50
    laser_prehistory_residual_pc = 20 / 100
    laser_integral_residual_pc = 1 / 100
    laser_length_residual_ind = 5
    left_limit = 100 #  ind
    right_limit = 20 #  ind

    def __init__(self, shotn, is_plasma, config_name, missing=None):
        self.loaded = False
        self.shotn = shotn
        self.is_plasma = is_plasma
        self.cofig_name = config_name
        if not os.path.isdir(self.config_path):
            self.error = 'Configuration path not found.'
            return
        if not os.path.isdir(self.db_path):
            self.error = 'Database path not found.'
            return
        config_full_name = '%s%s%s' % (self.config_path, self.cofig_name, self.extension)
        if not os.path.isfile(config_full_name):
            self.error = 'Configuration file not found.'
            return
        self.config = {}
        with open(config_full_name, 'r') as config_file:
            obj = ijson.kvitems(config_file, '', use_float=True)
            for k, v in obj:
                self.config[k] = v
        if missing is None:
            missing = [[] for board in range(len(self.config['adc']['sync']))]
        self.missing = missing
        self.header = {}
        self.data = []
        self.laser_count = 0
        self.loaded = self.load()
        self.processed = []

    def load(self):
        print('loading shot...')
        if self.is_plasma:
            shot_folder = '%splasma/%05d' % (self.db_path, self.shotn)
        else:
            shot_folder = '%sdebug/%05d' % (self.db_path, self.shotn)
        if not os.path.isdir(shot_folder):
            print('Requested shotn is missing.')
            return False
        header_path = '%s/header%s' % (shot_folder, self.extension)
        if not os.path.isfile(header_path):
            print('Shot is missing header file.')
            return False
        with open('%s/header.json' % shot_folder, 'r') as header_file:
            obj = ijson.kvitems(header_file, '', use_float=True)
            for k, v in obj:
                self.header[k] = v

        for board_ind in range(len(self.header['boards'])):
            if not os.path.isfile('%s/%d%s' % (shot_folder, board_ind, self.extension)):
                print('Requested shot is missing requested board file.')
                return False
            with open('%s/%d%s' % (shot_folder, board_ind, self.extension), 'rb') as board_file:
                event_ind = 0
                self.data.append([])
                for event in ijson.items(board_file, 'item', use_float=True):
                    while event_ind in self.missing[board_ind]:
                        self.data[board_ind].append({
                            'captured_bad': True
                        })
                        event_ind += 1
                    self.data[board_ind].append(event['groups'])
                    event_ind += 1
                while event_ind in self.missing[board_ind]:
                    self.data[board_ind].append({
                        'captured_bad': True
                    })
                    event_ind += 1
            print('Board %d loaded.' % board_ind)
        print('All data is loaded.')
        return self.check_raw_integrity()

    def check_raw_integrity(self):
        self.laser_count = len(self.data[0])
        for board_ind in range(1, len(self.data)):
            if len(self.data[board_ind]) != self.laser_count:
                print('Boards recorded different number of events! %d vs %d' %
                      (len(self.data[board_ind]), self.laser_count))
                # return False
                print('\n\n\n WARNING! check failed but commented for debug!\n')
                laser_count = min(self.laser_count, len(self.data[board_ind]))

        print('Total event count = %d.' % self.laser_count)
        return True

    def process_shot(self):
        print('Processing shot...')
        freq = float(self.header['frequency'])  # GS/s
        time_step = 1 / freq  # nanoseconds

        for event_ind in range(self.laser_count):
            bad_flag = False
            # print('Event %d' % event_ind)
            laser, laser_bad = self.process_laser_event(event_ind, time_step)
            bad_flag = bad_flag or laser_bad
            proc_event = {
                'laser': laser,
                'poly': {},
                'processed_bad': bad_flag
            }
            for poly in self.config['poly']:
                proc_event['poly'][poly['ind']] = self.process_poly_event(event_ind, time_step, poly, laser)
                break  # debug!

            self.processed.append(proc_event)
        self.save_processed()

    def save_processed(self):
        print('Saving processed data...')
        filepath = 'd:/data/signals/%05d.json' % self.shotn
        with open(filepath, 'w') as file:
            file.write('{\n "common": ')
            common = {
                'freq': self.header['frequency']
            }
            json.dump(common, file)

            file.write(', \n "data": [')
            for event in self.processed[:-1]:
                json.dump(event, file)
                file.write(',')

            json.dump(self.processed[-1], file)
            file.write(']\n}')
        print('completed.')

    def ch_to_gr(self, ch):
        return ch // self.ch_per_group, ch % self.ch_per_group

    def integrate_energy(self, signal, time_step, zero):
        res = 0.0
        flag = False
        integration_stop = -1
        for i in range(len(signal) - 1):
            if signal[i] - zero >= self.header['triggerThreshold']:
                flag = True
            res += time_step * (signal[i] + signal[i + 1] - 2 * zero) * 0.5  # ns*mV
            if flag and signal[i + 1] - zero < 0:
                integration_stop = i
                break
        else:
            print('Warning! Energy integration failed to stop.')
            exit()
        return res, integration_stop

    def process_laser_event(self, event_ind, time_step):
        bad_flag = False
        laser = {
            'boards': [],
            'ave': {
                'pre_std': 0,
                'int': 0,
                'int_len': 0
            }
        }
        board_count = 0
        for board_ind in range(len(self.data)):
            # print('Board %d' % board_ind)
            if 'captured_bad' in self.data[board_ind][event_ind] and \
                    self.data[board_ind][event_ind]['captured_bad']:
                laser['boards'].append({
                    'captured_bad': True
                })
                bad_flag = True
                continue
            adc_gr, adc_ch = self.ch_to_gr(self.config['adc']['sync'][board_ind]['ch'])
            signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            front_ind = find_front_findex(signal, self.header['triggerThreshold'])
            integration_limit = math.floor(front_ind) - self.config['adc']['prehistorySep']
            if integration_limit < self.left_limit:
                print('Warning, sync signal is too close to the left.')
                bad_flag = True
            zero = statistics.fmean(signal[:integration_limit])
            maximum = float('-inf')
            minimum = float('inf')
            for cell in signal:
                maximum = max(maximum, cell)
                minimum = min(minimum, cell)
            if minimum - self.offscale_threshold < self.header['offset'] - self.adc_baseline or \
                    maximum + self.offscale_threshold > self.header['offset'] + self.adc_baseline:
                print('Warning! sync signal offscale!')
                bad_flag = True
            integral, stop_ind = self.integrate_energy(signal[integration_limit:], time_step, zero)
            laser['boards'].append({
                'sync_ind': front_ind,
                'sync_ns': front_ind * time_step,
                'zero_lvl': zero,
                'pre_std': statistics.stdev(signal[:integration_limit], zero),
                'min': minimum,
                'max': maximum,
                'int': integral,
                'int_len': stop_ind
            })
            laser['ave']['pre_std'] += laser['boards'][-1]['pre_std']
            laser['ave']['int'] += integral
            laser['ave']['int_len'] += stop_ind
            board_count += 1
        laser['ave']['pre_std'] /= board_count
        laser['ave']['int'] /= board_count
        laser['ave']['int_len'] /= board_count
        for board_ind in range(len(self.data)):
            if 'captured_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['captured_bad']:
                continue
            if math.fabs(laser['ave']['pre_std'] - laser['boards'][board_ind]['pre_std']) / \
                    laser['ave']['pre_std'] > self.laser_prehistory_residual_pc:
                print('Warning! Boards prehistory differ too much for event %d' % event_ind)
                bad_flag = True
            if math.fabs(laser['ave']['int'] - laser['boards'][board_ind]['int']) / \
                    laser['ave']['int'] > self.laser_integral_residual_pc:
                print('Warning! Boards integrals differ too much for event %d' % event_ind)
                bad_flag = True
            if math.fabs(laser['ave']['int_len'] - laser['boards'][board_ind]['int_len']) > \
                    self.laser_length_residual_ind:
                print('Warning! Boards integral length differ too much for event %d' % event_ind)
                bad_flag = True
        return laser, bad_flag

    def process_poly_event(self, event_ind, time_step, poly, laser):
        res = {
            'ch': []
        }
        for sp_ch in poly['channels']:
            bad_flag = False
            board_ind = sp_ch['adc']
            if 'captured_bad' in self.data[board_ind][event_ind] and self.data[board_ind][event_ind]['captured_bad']:
                res['ch'].append({
                    'processed_bad': True
                })
                continue
            if 'processed_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['processed_bad']:
                res['ch'].append({
                    'processed_bad': True
                })
                continue
            if 'skip' in sp_ch and sp_ch['skip']:
                res['ch'].append({
                    'processed_bad': True
                })
                continue
            adc_gr, adc_ch = self.ch_to_gr(sp_ch['ch'])
            signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            integration_from = math.floor(laser['boards'][board_ind]['sync_ind'] + sp_ch['int_from_ns'] /
                                          time_step)
            integration_to = math.ceil(laser['boards'][board_ind]['sync_ind'] + sp_ch['int_to_ns'] /
                                        time_step)
            if integration_from < self.left_limit:
                print('Warning! Integration limit is too close to the left for Poly %d channel %d  in event %d!' %
                      (poly['ind'], sp_ch['ch'], event_ind))
                bad_flag = True
            if integration_to > self.header['eventLength'] - self.right_limit:
                print('Warning! Integration limit is too close to the right for Poly %d channel %d  in event %d!' %
                      (poly['ind'], sp_ch['ch'], event_ind))
                bad_flag = True
            zero = statistics.fmean(signal[:integration_from])
            maximum = float('-inf')
            minimum = float('inf')
            for cell in signal:
                maximum = max(maximum, cell)
                minimum = min(minimum, cell)
            if minimum - self.offscale_threshold < self.header['offset'] - self.adc_baseline or \
                    maximum + self.offscale_threshold > self.header['offset'] + self.adc_baseline:
                print('Warning! Poly %d channel %d offscale in event %d!' % (poly['ind'], sp_ch['ch'], event_ind))
                bad_flag = True
            integral = 0
            if not bad_flag:
                for cell in range(integration_from, integration_to - 1):
                    integral += time_step * (signal[cell] + signal[cell + 1] - 2 * zero) * 0.5  # ns*mV
            photoelectrons = integral * 1e-3 * 1e-9 / (self.config['preamp']['apdGain'] *
                                                       self.config['preamp']['charge'] *
                                                       self.config['preamp']['feedbackResistance'] *
                                                       sp_ch['fast_gain'])
            if self.config['preamp']['voltageDivider']:
                photoelectrons *= 2
            res['ch'].append({
                'from': integration_from,
                'to': integration_to,
                'zero_lvl': zero,
                'pre_std': statistics.stdev(signal[:integration_from], zero),
                'min': minimum,
                'max': maximum,
                'int': integral,
                'ph_el': photoelectrons,
                'processed_bad': bad_flag
            })
        return res

    def plot(self, event_ind, poly):
        import matplotlib as plt
        fig, ax = plt.subplots()
        '''
        for sp_ch in poly['channels']:
            board_ind = sp_ch['adc']
            if 'captured_bad' in self.data[board_ind][event_ind] and self.data[board_ind][event_ind]['captured_bad']:
                continue
            #if 'processed_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['processed_bad']:
            #    continue
            if 'skip' in sp_ch and sp_ch['skip']:
                continue
            adc_gr, adc_ch = self.ch_to_gr(sp_ch['ch'])
            signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            start = self.processed[event_ind]['laser']['boards'][board_ind]['sync_ns']
            plt.plot(timeline, averaged[ch_ind], label='ADC_ch %d' % channels[ch_ind])

        '''
        plt.ylabel('signal, mV')
        plt.xlabel('timeline, ns')
        plt.title('title')
        plt.xlim(-5, 175)
        plt.ylim(-50, 2300)
        #filename = '../figures/poly%d/ave_board%d_ch%s' % (poly, board_idx, channels)
        ax.legend()
        plt.grid(color='k', linestyle='-', linewidth=1)
        #plt.savefig('%s.png' % filename, dpi=600)
        plt.close(fig)
