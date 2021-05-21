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
    RAW_FOLDER = 'raw/'
    SIGNAL_FOLDER = 'signal/'
    CONFIG_FOLDER = 'config/'
    HEADER_FILE = 'header'
    FILE_EXT = '.json'


    # move to config!
    group_per_board = 8
    ch_per_group = 2
    adc_baseline = 1250
    offscale_threshold = 50
    laser_prehistory_residual_pc = 20 / 100
    laser_integral_residual_pc = 1 / 100
    laser_length_residual_ind = 5
    left_limit = 100  # ind
    right_limit = 20  # ind

    def __init__(self, db_path, shotn, is_plasma, config_name, global_db):
        self.shotn = shotn
        self.is_plasma = is_plasma
        self.config_name = config_name
        if not os.path.isdir(db_path):
            self.error = 'Local database path not found.'
            return
        if not os.path.isdir(global_db):
            self.error = 'Global database path not found.'
            return
        self.db_path = db_path
        if not os.path.isdir('%s%s' % (global_db, self.CONFIG_FOLDER)):
            self.error = 'Configuration path not found.'
            return
        config_full_name = '%s%s%s%s' % (global_db, self.CONFIG_FOLDER, self.config_name, self.FILE_EXT)
        if not os.path.isfile(config_full_name):
            self.error = 'Configuration file not found.'
            return
        self.config = {}
        with open(config_full_name, 'r') as config_file:
            obj = ijson.kvitems(config_file, '', use_float=True)
            for k, v in obj:
                self.config[k] = v

        self.header = {}
        self.data = []
        self.laser_count = 0
        self.time_step = 0
        self.loaded = False
        self.processed = []
        if not self.load():
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            fuck

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        self.data = []
        del self.data
        self.processed = []
        del self.processed
        self.config = {}
        del self.config
        self.header = {}
        del self.header

    def load(self):
        self.processed = []
        shot_folder = '%s%s%05d/' % (self.db_path, self.RAW_FOLDER, self.shotn)
        if not os.path.isdir(shot_folder):
            print('Requested shotn is missing.')
            print(shot_folder)
            return False
        header_path = '%s%s%s' % (shot_folder, self.HEADER_FILE, self.FILE_EXT)
        if not os.path.isfile(header_path):
            print('Shot is missing header file.')
            return False
        with open(header_path, 'rb') as header_file:
            obj = ijson.kvitems(header_file, '', use_float=True)
            for k, v in obj:
                self.header[k] = v

        self.load_raw()
        return True

    def load_raw(self):
        self.loaded = False
        self.data = []
        freq = float(self.header['frequency'])  # GS/s
        self.time_step = 1 / freq  # nanoseconds
        print('loading raw shot...')
        if self.is_plasma:
            shot_folder = '%s%s%05d/' % (self.db_path, self.RAW_FOLDER, self.shotn)
        else:
            shot_folder = '%s%s%05d/' % (self.db_path,  self.RAW_FOLDER, self.shotn)
        for board_ind in range(len(self.header['boards'])):
            if not os.path.isfile('%s/%d%s' % (shot_folder, board_ind, self.FILE_EXT)):
                print('Requested shot is missing requested board file.')
                return False
            skip = True
            with open('%s/%d%s' % (shot_folder, board_ind, self.FILE_EXT), 'rb') as board_file:
                self.data.append([])
                for event in ijson.items(board_file, 'item', use_float=True):
                    if skip:
                        skip = False
                        continue
                    self.data[board_ind].append(event['groups'])
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
        self.loaded = True
        return True

    def process_shot(self, event_indexes, delays):
        print('Processing shot...')
        for event_ind_ind in range(len(event_indexes)):
            event_ind = event_indexes[event_ind_ind]
            # print('Event %d' % event_ind)
            laser, error = self.process_laser_event(event_ind)
            if self.laser_count > 1:
                timestamp = self.data[0][event_ind][0]['timestamp'] - self.data[0][0][0]['timestamp'] + self.config['adc']['first_shot']
            else:
                timestamp = -999
            proc_event = {
                'timestamp': timestamp,
                'laser': laser,
                'error': error
            }
            if error is None:
                proc_event['1064'] = []
                proc_event['1047'] = []
                for poly in self.config['poly']:
                    proc_event['1064'].append(self.process_poly_event(event_ind, poly, laser))
                    proc_event['1047'].append(self.process_poly_event(event_ind, poly, laser, delays[event_ind_ind]))
                self.processed.append(proc_event)
            else:
                self.processed.append({
                    'error': 'laser'
                })

        #self.save_processed()
        self.export_processed()

    def export_processed(self):
        print('Saving processed data...')
        filepath = '%s%s%05d.json' % (self.db_path, 'export/', self.shotn)
        with open(filepath, 'w') as file:
            file.write('[')
            for event in self.processed[:-1]:
                json.dump(event, file)
                file.write(',')

            if len(self.processed) > 0:
                json.dump(self.processed[-1], file)
            file.write(']')
        print('completed.')

    def save_processed(self):
        print('Saving processed data...')
        filepath = '%s%s%05d%s' % (self.db_path, self.SIGNAL_FOLDER, self.shotn, self.FILE_EXT)
        with open(filepath, 'w') as file:
            file.write('{\n "common": ')
            common = {
                'header': self.header,
                'config_name': self.config_name,
                'config': self.config,
                'isPlasma': self.is_plasma
            }
            json.dump(common, file)

            file.write(', \n "data": [')
            for event in self.processed[:-1]:
                json.dump(event, file)
                file.write(',')

            if len(self.processed) > 0:
                json.dump(self.processed[-1], file)
            file.write(']\n}')
        print('completed.')

    def ch_to_gr(self, ch):
        return ch // self.ch_per_group, ch % self.ch_per_group

    def integrate_energy(self, signal, zero):
        res = 0.0
        flag = False
        integration_stop = -1
        print('\n\n')
        print(zero)
        for i in range(len(signal) - 1):
            if signal[i] - zero >= 20:#self.header['triggerThreshold']:
                flag = True
                start = i
            res += self.time_step * (signal[i] + signal[i + 1] - 2 * zero) * 0.5  # ns*mV
            #if flag and signal[i + 1] - zero < 0:
            if flag and i - start > 100:
                integration_stop = i
                break
        else:
            print('Warning! Energy integration failed to stop.')
            print('WTF???', zero)
            return res, -integration_stop
        print('integration ok.')
        return res, integration_stop

    def process_laser_event(self, event_ind):
        error = None
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
                error = 'bad captured'
                continue
            adc_gr, adc_ch = self.ch_to_gr(self.config['adc']['sync'][board_ind]['ch'])
            signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            front_ind = find_front_findex(signal, self.header['triggerThreshold'])
            integration_limit = math.floor(front_ind) - self.config['adc']['prehistorySep']
            if integration_limit < self.left_limit:
                error = 'Sync left'
            zero = statistics.fmean(signal[:integration_limit])
            maximum = float('-inf')
            minimum = float('inf')
            for cell in signal:
                maximum = max(maximum, cell)
                minimum = min(minimum, cell)
            if minimum - self.offscale_threshold < self.header['offset'] - self.adc_baseline or \
                    maximum + self.offscale_threshold > self.header['offset'] + self.adc_baseline:
                error = 'sync offscale'
            integral, stop_ind = self.integrate_energy(signal[integration_limit:], zero)
            if stop_ind < 0:
                error = 'integration failed to stop'
                stop_ind = -stop_ind
            laser['boards'].append({
                'sync_ind': front_ind,
                'sync_ns': front_ind * self.time_step,
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
                error = 'prehistory differ'
            if math.fabs(laser['ave']['int'] - laser['boards'][board_ind]['int']) / \
                    laser['ave']['int'] > self.laser_integral_residual_pc:
                error = 'integrals differ'
            if math.fabs(laser['ave']['int_len'] - laser['boards'][board_ind]['int_len']) > \
                    self.laser_length_residual_ind:
                error = 'integral length differ'
        if error is not None:
            print(error, event_ind)
            print('\n HERE \n')
        return laser, error

    def process_poly_event(self, event_ind, poly, laser, delay=None):
        res = []
        for ch_ind in range(len(poly['channels'])):
            error = None
            sp_ch = poly['channels'][ch_ind]
            board_ind = sp_ch['adc']
            if 'captured_bad' in self.data[board_ind][event_ind] and self.data[board_ind][event_ind]['captured_bad']:
                res.append({
                    'error': 'bad captured'
                })
                continue
            if 'skip' in sp_ch and sp_ch['skip']:
                res.append({
                    'error': 'skip'
                })
                continue
            adc_gr, adc_ch = self.ch_to_gr(sp_ch['ch'])
            signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            integration_from = math.floor(laser['boards'][board_ind]['sync_ind'] +
                                          (poly['delay'] + self.config['common']['ch_delay'] * ch_ind) / self.time_step)
            if integration_from < self.left_limit:
                error = 'left boundary'
            zero = statistics.fmean(signal[:integration_from])
            pre_std = statistics.stdev(signal[:integration_from], zero)
            maximum = float('-inf')
            minimum = float('inf')
            for cell in signal:
                maximum = max(maximum, cell)
                minimum = min(minimum, cell)
            if minimum - self.offscale_threshold < self.header['offset'] - self.adc_baseline:
                error = 'minimum %.1f' % minimum
            elif maximum + self.offscale_threshold > self.header['offset'] + self.adc_baseline:
                error = 'maximum %.1f' % maximum
            if delay is not None:
                integration_from = math.floor(laser['boards'][board_ind]['sync_ind'] +
                                          (delay + 2 - self.config['common']['integrationTime'] * 0.5 + self.config['common']['ch_delay'] * ch_ind) / self.time_step)
            integration_to = integration_from + math.ceil(self.config['common']['integrationTime'] / self.time_step)
            if delay is not None:
                integration_to = integration_from + math.ceil((self.config['common']['integrationTime'] - 12) / self.time_step)
            if integration_to > self.header['eventLength'] - self.right_limit:
                error = 'right boundary'
            integral = 0
            if error is None:
                for cell in range(integration_from, integration_to - 1):
                    integral += self.time_step * (signal[cell] + signal[cell + 1] - 2 * zero) * 0.5  # ns*mV
            else:
                print(error)
            photoelectrons = integral * 1e-3 * 1e-9 / (self.config['preamp']['apdGain'] *
                                                       self.config['preamp']['charge'] *
                                                       self.config['preamp']['feedbackResistance'] *
                                                       sp_ch['fast_gain'])
            if self.config['preamp']['voltageDivider']:
                photoelectrons *= 2

            err2 = math.pow(pre_std, 2) * 6715 * 0.0625 - 1.14e4 * 0.0625
            res.append({
                'from': integration_from,
                'to': integration_to,
                'zero_lvl': zero,
                'pre_std': pre_std,
                'min': minimum,
                'max': maximum,
                'int': integral,
                'ph_el': photoelectrons,
                'err': math.sqrt(math.fabs(err2) + math.fabs(photoelectrons) * 4),
                'error': error,
                'raw': signal
            })
        return res
