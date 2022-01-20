import os
import ijson
import json
import statistics
import math
import msgpack


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
    PLASMA_FOLDER = 'plasma/'
    DEBUG_FOLDER = 'debug/'
    RAW_FOLDER = 'raw/'
    SIGNAL_FOLDER = 'signal/'
    CONFIG_FOLDER = 'config/'
    HEADER_FILE = 'header'
    JSON_EXT = '.json'
    BINARY_EXT = '.msgpk'


    # move to config!
    group_per_board = 8
    ch_per_group = 2
    adc_baseline = 1250
    offscale_threshold = 50
    laser_prehistory_residual_pc = 20  # mv
    laser_integral_residual_pc = 5 / 100
    laser_length_residual_ind = 5
    left_limit = 100  # ind
    right_limit = 20  # ind

    def __init__(self, db_path, shotn, is_plasma, config_name):
        self.shotn = shotn
        self.is_plasma = is_plasma
        self.config_name = config_name
        if not os.path.isdir(db_path):
            self.error = 'Database path not found.'
            return
        self.db_path = db_path
        if not os.path.isdir('%s%s' % (self.db_path, self.CONFIG_FOLDER)):
            self.error = 'Configuration path not found.'
            return
        config_full_name = '%s%s%s%s' % (self.db_path, self.CONFIG_FOLDER, self.config_name, self.JSON_EXT)
        if not os.path.isfile(config_full_name):
            self.error = 'Configuration file not found.'
            return
        self.config = {}
        with open(config_full_name, 'r') as config_file:
            obj = ijson.kvitems(config_file, '', use_float=True)
            for k, v in obj:
                self.config[k] = v

        self.header = {}
        self.version = 1
        self.data = []
        self.laser_count = 0
        self.time_step = 0
        self.loaded = False
        self.processed = []
        if self.is_plasma:
            self.prefix = '%s%s' % (self.db_path, self.PLASMA_FOLDER)
        else:
            self.prefix = '%s%s' % (self.db_path, self.DEBUG_FOLDER)
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
        shot_folder = '%s%s%05d/' % (self.prefix, self.RAW_FOLDER, self.shotn)
        if not os.path.isdir(shot_folder):
            print('Requested %d shotn is missing: %s' % (self.shotn, shot_folder))
            return False
        header_path = '%s%s%s' % (shot_folder, self.HEADER_FILE, self.JSON_EXT)
        if not os.path.isfile(header_path):
            print('Shot is missing header file.')
            return False
        with open(header_path, 'rb') as header_file:
            obj = ijson.kvitems(header_file, '', use_float=True)
            for k, v in obj:
                self.header[k] = v

        if 'version' in self.header:
            self.version = self.header['version']

        signal_path = '%s%s%05d%s' % (self.prefix, self.SIGNAL_FOLDER, self.shotn, self.JSON_EXT)
        if os.path.isfile(signal_path):
            print('Loading existing processed signals.')
            with open(signal_path, 'rb') as signal_file:
                obj = ijson.items(signal_file, 'common.config_name', use_float=True)
                for val in obj:
                    if val == self.config_name:
                        signal_file.seek(0)
                        obj = ijson.items(signal_file, 'data.item', use_float=True)
                        for event in obj:
                            self.processed.append(event)
                        return True
                    else:
                        print('existing file has different config')

        self.load_raw()
        self.process_shot()
        return True

    def load_raw(self):
        self.loaded = False
        self.data = []
        freq = float(self.header['frequency'])  # GS/s
        self.time_step = 1 / freq  # nanoseconds
        print('loading raw shot...')
        if self.is_plasma:
            shot_folder = '%s%s%s%05d/' % (self.db_path, self.PLASMA_FOLDER, self.RAW_FOLDER, self.shotn)
        else:
            shot_folder = '%s%s%s%05d/' % (self.db_path, self.DEBUG_FOLDER, self.RAW_FOLDER, self.shotn)
        for board_ind in range(len(self.config['adc']['sync'])):
            extension = self.JSON_EXT
            if self.version == 2:
                extension = self.BINARY_EXT

            if not os.path.isfile('%s%d%s' % (shot_folder, board_ind, extension)):
                print('Requested shot is missing requested board file %s.' % '%s%d%s' % (shot_folder, board_ind, extension))
                return False
            with open('%s/%d%s' % (shot_folder, board_ind, extension), 'rb') as board_file:
                self.data.append([])
                if self.version == 1:
                    for event in ijson.items(board_file, 'item', use_float=True):
                        self.data[board_ind].append(event['groups'])
                else:
                    self.data[board_ind] = msgpack.unpackb(board_file.read())
            print('Board %d loaded.' % board_ind)
        print('All data is loaded.')
        return self.check_raw_integrity()

    def check_raw_integrity(self):
        self.laser_count = len(self.data[0])
        for board_ind in range(len(self.config['adc']['sync'])):
            if len(self.data[board_ind]) != self.laser_count:
                print('Boards recorded different number of events! %d vs %d' %
                      (len(self.data[board_ind]), self.laser_count))
                # return False
                print('\n\n\n WARNING! check failed but commented for debug!\n')
                laser_count = min(self.laser_count, len(self.data[board_ind]))

        print('Total event count = %d.' % self.laser_count)
        self.loaded = True
        return True

    def process_shot(self):
        print('Processing shot...')
        if self.version == 1:
            combiscope_zero = self.data[0][0][0]['timestamp'] - self.config['adc']['first_shot']
        else:
            combiscope_zero = self.data[0][0]['t'] - self.config['adc']['first_shot']
        expect_sync = True
        for event_ind in range(self.laser_count):
            # print('Event %d' % event_ind)
            laser, error = self.process_laser_event(event_ind, expect_sync)
            if 'sync' in laser and laser['sync']:
                if self.version == 1:
                    combiscope_zero = self.data[0][event_ind][1]['timestamp']
                else:
                    combiscope_zero = self.data[0][event_ind]['t']
                for correction_ind in range(event_ind):
                    if self.version == 1:
                        self.processed[correction_ind]['timestamp'] = self.data[0][correction_ind][1]['timestamp'] - combiscope_zero
                    else:
                        self.processed[correction_ind]['timestamp'] = self.data[0][correction_ind]['t'] - combiscope_zero
                expect_sync = False
            if self.laser_count > 1:
                #timestamp = self.data[0][event_ind][0]['timestamp'] - self.data[0][0][0]['timestamp'] + self.config['adc']['first_shot']
                if self.version == 1:
                    timestamp = self.data[0][event_ind][1]['timestamp'] - combiscope_zero
                else:
                    timestamp = self.data[0][event_ind]['t'] - combiscope_zero
            else:
                timestamp = -999
            proc_event = {
                'timestamp_dummy': self.config['adc']['first_shot'] + (event_ind - 1) * 3.03030303,
                'timestamp': timestamp,
                'laser': laser,
                'poly': {},
                'error': error
            }
            if error is None:
                for poly in self.config['poly']:
                    proc_event['poly'][('%d' % poly['ind'])] = self.process_poly_event(event_ind, poly, laser)
            self.processed.append(proc_event)

        self.save_processed()

    def save_processed(self):
        print('Saving processed data...')
        filepath = '%s%s%05d%s' % (self.prefix, self.SIGNAL_FOLDER, self.shotn, self.JSON_EXT)
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
        for i in range(len(signal) - 1):
            if signal[i] - zero >= self.header['triggerThreshold']:
                flag = True
                start = i
            res += self.time_step * (signal[i] + signal[i + 1] - 2 * zero) * 0.5  # ns*mV
            # if flag and signal[i + 1] - zero < 0:
            if flag and i - start > 177:
                integration_stop = i
                break
        else:
            print('Warning! Energy integration failed to stop.')
            return res, -integration_stop
        return res, integration_stop

    def process_laser_event(self, event_ind, expect_sync=True):
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
        sync_event = []
        for board_ind in range(len(self.config['adc']['sync'])):
            # print('Board %d' % board_ind)
            if self.version == 1:
                adc_gr, adc_ch = self.ch_to_gr(self.config['adc']['sync'][board_ind]['ch'])
                signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            else:
                signal = self.data[board_ind][event_ind]['ch'][self.config['adc']['sync'][board_ind]['ch']]
            maximum = float('-inf')
            minimum = float('inf')
            for cell in signal:
                maximum = max(maximum, cell)
                minimum = min(minimum, cell)
            front_ind = find_front_findex(signal, signal[0] + self.header['triggerThreshold'])
            if front_ind == -1:
                sync_event.append(True)
                error = 'Laser signal does not reach threshold.'
                laser['boards'].append({
                    'min': minimum,
                    'max': maximum
                })
                continue
            else:
                sync_event.append(False)
            integration_limit = math.floor(front_ind) - self.config['adc']['prehistorySep']
            if integration_limit < self.left_limit:
                error = 'Sync left'
            zero = statistics.fmean(signal[:integration_limit])
            if minimum - self.offscale_threshold < self.header['offset'] - self.adc_baseline or \
                    maximum + self.offscale_threshold > self.header['offset'] + self.adc_baseline:
                error = 'sync offscale'

            is_new_FPU = False
            if is_new_FPU:
                stop_ind = integration_limit + math.ceil(self.config['common']['integrationTime'] / self.time_step)
                integral = sum(sig - zero for sig in signal[integration_limit: stop_ind]) * self.time_step
            else:
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
            #laser['ave']['int_len'] += stop_ind
            board_count += 1
        sync = True
        for board_ind in range(len(self.config['adc']['sync'])):
            if 'captured_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['captured_bad']:
                continue
            if not sync_event[board_ind]:
                sync = False
        if expect_sync and sync:
            laser['sync'] = True
            print('Globus synchronization found.%d' % event_ind)
            return laser, error

        if board_count < len(self.data):
            error = 'not all boards got laser signal'
        else:
            laser['ave']['pre_std'] /= board_count
            laser['ave']['int'] /= board_count
            #laser['ave']['int_len'] /= board_count
            laser['ave']['int_len'] = math.ceil(self.config['common']['integrationTime'] / self.time_step)
            for board_ind in range(len(self.config['adc']['sync'])):
                if 'captured_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['captured_bad']:
                    continue
                if laser['boards'][board_ind]['pre_std'] > self.laser_prehistory_residual_pc:
                    error = 'too large prehistory error'
                if math.fabs(laser['ave']['int'] - laser['boards'][board_ind]['int']) / \
                        laser['ave']['int'] > self.laser_integral_residual_pc:
                    error = 'integrals differ'
        if error is not None:
            print(error, event_ind)
        return laser, error

    def process_poly_event(self, event_ind, poly, laser):
        res = {
            'ch': []
        }
        for ch_ind in range(len(poly['channels'])):
            error = None
            sp_ch = poly['channels'][ch_ind]
            board_ind = sp_ch['adc']

            if 'skip' in sp_ch and sp_ch['skip']:
                res['ch'].append({
                    'error': 'skip'
                })
                continue
            adc_gr, adc_ch = self.ch_to_gr(sp_ch['ch'])
            if self.version == 1:
                signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            else:
                signal = self.data[board_ind][event_ind]['ch'][sp_ch['ch']]
            integration_from = math.floor(laser['boards'][board_ind]['sync_ind'] +
                                          (poly['delay'] + self.config['common']['ch_delay'] * ch_ind) / self.time_step)
            integration_to = integration_from + math.ceil(self.config['common']['integrationTime'] / self.time_step)
            if integration_from < self.left_limit:
                error = 'left boundary'
            if integration_to > self.header['eventLength'] - self.right_limit:
                error = 'right boundary'
            zero = statistics.fmean(signal[:integration_from])
            maximum = float('-inf')
            minimum = float('inf')
            for cell in signal:
                maximum = max(maximum, cell)
                minimum = min(minimum, cell)
            if minimum - self.offscale_threshold < self.header['offset'] - self.adc_baseline:
                error = 'minimum %.1f, index = %d, poly = %d, ch = %d' % (minimum, event_ind, poly['ind'], ch_ind + 1)
            elif maximum + self.offscale_threshold > self.header['offset'] + self.adc_baseline:
                error = 'maximum %.1f, index = %d, poly = %d, ch = %d' % (minimum, event_ind, poly['ind'], ch_ind + 1)
            integral = 0
            if error is None:
                for cell in range(integration_from, integration_to - 1):
                    integral += self.time_step * (signal[cell] + signal[cell + 1] - 2 * zero) * 0.5  # ns*mV
            else:
                print(error)
            if 'matchingFastGain' not in self.config['preamp']:
                matching_gain = 1
                print('WARNING! forgotten preamp gain')
                fuck
            else:
                matching_gain = self.config['preamp']['matchingFastGain']
            photoelectrons = integral * 1e-3 * 1e-9 / (self.config['preamp']['apdGain'] *
                                                       self.config['preamp']['charge'] *
                                                       self.config['preamp']['feedbackResistance'] *
                                                       sp_ch['fast_gain'] *
                                                       matching_gain)
            if self.config['preamp']['voltageDivider']:
                photoelectrons *= 2
            pre_std = statistics.stdev(signal[:integration_from], zero)
            err2 = math.pow(pre_std, 2) * 6715 * 0.0625 - 1.14e4 * 0.0625
            res['ch'].append({
                'from': integration_from,
                'to': integration_to,
                'zero_lvl': zero,
                'pre_std': pre_std,
                'min': minimum,
                'max': maximum,
                'int': integral,
                'ph_el': photoelectrons,
                'err': math.sqrt(math.fabs(err2) + math.fabs(photoelectrons) * 4),
                'error': error
            })
        return res
