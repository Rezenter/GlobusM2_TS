import os
import ijson
import json
import statistics
import math
import msgpack
import phys_const


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
    offscale_threshold = 25  # mv
    laser_prehistory_residual_pc = 20  # mv
    laser_integral_residual_pc = 5 / 100
    laser_length_residual_ind = 5
    left_limit = 100  # ind
    right_limit = 20  # ind

    def __init__(self, db_path, shotn, is_plasma, config_name):
        print('raw init ', shotn)
        self.shotn = shotn
        self.is_plasma = is_plasma
        self.config_name = config_name
        self.error = ''
        if not os.path.isdir(db_path):
            self.error = 'Database path not found.'
            return
        self.db_path = db_path
        if not os.path.isdir('%s%s' % (self.db_path, self.CONFIG_FOLDER)):
            self.error = 'Configuration path not found.'
            return

        config_full_name = '%s%s%s%s' % (self.db_path, 'config_cpp/', self.config_name, self.JSON_EXT)
        if not os.path.isfile(config_full_name):
            config_full_name = '%s%s%s%s' % (self.db_path, self.CONFIG_FOLDER, self.config_name, self.JSON_EXT)
            if not os.path.isfile(config_full_name):
                self.error = 'Configuration file not found. %s' % config_full_name
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
        print('load raw')
        if not self.load():
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            fuck
        print('raw proc OK?')

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

        if False and os.path.isfile(signal_path):
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

        if self.version >= 6:
            freq = float(self.header['config']['fast adc']['frequency GHz'])
        else:
            freq = float(self.header['frequency'])  # GS/s
        self.time_step = 1 / freq  # nanoseconds
        print('loading raw shot...')
        if self.is_plasma:
            shot_folder = '%s%s%s%05d/' % (self.db_path, self.PLASMA_FOLDER, self.RAW_FOLDER, self.shotn)
        else:
            shot_folder = '%s%s%s%05d/' % (self.db_path, self.DEBUG_FOLDER, self.RAW_FOLDER, self.shotn)

        self.boards = []
        if self.version < 6:
            for board_ind in range(len(self.header['boards'])):
                self.header['boards'][board_ind]['laser_ch'] = self.config['adc']['sync'][board_ind]['ch']
                self.header['boards'][board_ind]['prehistorySep'] = self.config['adc']['prehistorySep']
                self.header['boards'][board_ind]['offset'] = self.header['offset']
            for poly in self.config['poly']:
                for ch in poly['channels']:
                    if ch['adc'] not in self.boards:
                        self.boards.append(ch['adc'])
        else:
            board_ind = 0
            for link in self.config['fast adc']['links']:
                for board in link:
                    if self.header['boards'][board_ind]['ser'] != board['serial']:
                        print(board_ind, self.header['boards'][board_ind]['ser'], board['serial'])
                        fuck

                    self.header['boards'][board_ind]['laser_ch'] = board['laser_ch']
                    self.header['boards'][board_ind]['prehistorySep'] = board['prehistorySep']
                    self.header['boards'][board_ind]['offset'] = board['vertical offset']
                    self.header['triggerThreshold'] = 100

                    board_ind += 1
                    pass
            for poly in self.config['poly']:
                for ch in poly['channels']:
                    for gain in ch['fast']:
                        if gain['adc'] not in self.boards:
                            self.boards.append(gain['adc'])
        self.boards.sort()

        #for board_ind in range(len(self.config['adc']['sync'])):
        for board_ind in range(len(self.header['boards'])):
            self.data.append([])
            if board_ind in self.boards:
                extension = self.JSON_EXT
                if self.version >= 2:
                    extension = self.BINARY_EXT

                if not os.path.isfile('%s%d%s' % (shot_folder, board_ind, extension)):
                    print('Requested shot is missing requested board file %s.' % '%s%d%s' % (shot_folder, board_ind, extension))
                    return False
                with open('%s/%d%s' % (shot_folder, board_ind, extension), 'rb') as board_file:

                    if self.version <= 1:
                        for event in ijson.items(board_file, 'item', use_float=True):
                            self.data[board_ind].append(event['groups'])
                    else:
                        self.data[board_ind] = msgpack.unpackb(board_file.read())
                if self.version >= 3:
                    self.header['triggerThreshold'] = 100
                print('Board %d loaded.' % board_ind)
        return self.check_raw_integrity()

    def check_raw_integrity(self):
        self.laser_count = len(self.data[self.boards[0]])
        #for board_ind in range(len(self.config['adc']['sync'])):
        for board_ind in range(len(self.header['boards'])):
            if board_ind not in self.boards:
                continue
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
        if self.version <= 1:
            combiscope_zero = self.data[self.boards[0]][0][0]['timestamp'] - self.config['adc']['first_shot']
        elif 4 <= self.version:
            combiscope_zero = self.data[self.boards[0]][0]['t']
        else:
            combiscope_zero = self.data[self.boards[0]][0]['t'] - self.config['adc']['first_shot']
        expect_sync = True
        for event_ind in range(self.laser_count):

            laser, error = self.process_laser_event(event_ind, expect_sync)
            if 'sync' in laser and laser['sync']:
                if self.version <= 1:
                    combiscope_zero = self.data[self.boards[0]][event_ind][1]['timestamp']
                else:
                    combiscope_zero = self.data[self.boards[0]][event_ind]['t']
                for correction_ind in range(event_ind):
                    if self.version <= 1:
                        self.processed[correction_ind]['timestamp'] = self.data[self.boards[0]][correction_ind][1]['timestamp'] - combiscope_zero
                    if self.version >= 4:
                        self.processed[correction_ind]['timestamp'] = combiscope_zero
                    else:
                        self.processed[correction_ind]['timestamp'] = self.data[self.boards[0]][correction_ind]['t'] - combiscope_zero
                expect_sync = False
            if self.laser_count > 1:
                #timestamp = self.data[self.boards[0]][event_ind][0]['timestamp'] - self.data[self.boards[0]][0][0]['timestamp'] + self.config['adc']['first_shot']
                if self.version <= 1:
                    timestamp = self.data[self.boards[0]][event_ind][1]['timestamp'] - combiscope_zero
                elif self.version >= 4:
                    timestamp = self.data[self.boards[0]][event_ind]['t']
                else:
                    timestamp = self.data[self.boards[0]][event_ind]['t'] - combiscope_zero
            else:
                timestamp = -999

            if self.version < 6:
                dummy = self.config['adc']['first_shot'] + (event_ind - 1) * 3.03030303
            else:
                dummy = self.config['fast adc']['first_shot'] + (event_ind - 1) * 3.03030303
            proc_event = {
                'timestamp_dummy': dummy,
                'timestamp': timestamp,
                'laser': laser,
                'poly': {},
                'error': error
            }
            if error is None:
                for poly in self.config['poly']:
                    if self.version < 6:
                        proc_event['poly'][poly['serial']] = self.process_poly_event(event_ind, poly, laser)
                    else:
                        proc_event['poly'][poly['serial']] = self.process_poly_event(event_ind, poly, laser)
                        #proc_event['poly'][('%d' % poly['serial'])] = self.process_poly_event(event_ind, poly, laser)
            self.processed.append(proc_event)

        self.save_processed()

    def save_processed(self, filepath='', version=-1):
        print('Saving processed data...')
        if filepath == '':
            filepath = '%s%s%05d%s' % (self.prefix, self.SIGNAL_FOLDER, self.shotn, self.JSON_EXT)
        with open(filepath, 'w') as file:
            file.write('{\n "common": ')
            common = {
                'header': self.header,
                'config_name': self.config_name,
                'config': self.config,
                'isPlasma': self.is_plasma
            }
            if version != -1:
                common['version'] = version
            json.dump(common, file, indent=1)

            file.write(', \n "data": [')
            for event in self.processed[:-1]:
                json.dump(event, file, indent=1)
                file.write(',')

            if len(self.processed) > 0:
                json.dump(self.processed[-1], file, indent=1)
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

        #for board_ind in range(len(self.config['adc']['sync'])):
        for board_ind in range(len(self.header['boards'])):
            if board_ind not in self.boards:
                laser['boards'].append({})
                continue
            # print('Board %d' % board_ind)

            if self.version <= 1:
                adc_gr, adc_ch = self.ch_to_gr(self.config['adc']['sync'][board_ind]['ch'])
                signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            elif 4 <= self.version:
                signal = [self.header['boards'][board_ind]['offset'] - 1250 + v * 2500/4096 for v in self.data[board_ind][event_ind]['ch'][self.header['boards'][board_ind]['laser_ch']]]
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
            integration_limit = math.floor(front_ind) - self.header['boards'][board_ind]['prehistorySep']
            if integration_limit < self.left_limit:
                error = 'Sync left'
            zero = statistics.fmean(signal[:integration_limit])
            if minimum - self.offscale_threshold < self.header['boards'][board_ind]['offset'] - self.adc_baseline or \
                    maximum + self.offscale_threshold > self.header['boards'][board_ind]['offset'] + self.adc_baseline:
                #print(minimum, maximum, self.offscale_threshold, self.header['offset'], self.adc_baseline)
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
            if board_ind != 8:
                laser['ave']['pre_std'] += laser['boards'][-1]['pre_std']
                laser['ave']['int'] += integral
            else:
                print('Warning! T15 patch!', board_ind)
            #laser['ave']['int_len'] += stop_ind
            board_count += 1
        sync = True
        for i, board_ind in enumerate(self.boards):
            if 'captured_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['captured_bad']:
                continue
            if not sync_event[i]:
                sync = False
        if expect_sync and sync:
            laser['sync'] = True
            print('Globus synchronization found.%d' % event_ind)
            return laser, error

        if board_count < len(self.boards):
            #error = 'not all boards got laser signal'
            print('not all boards got laser signal, but commented for t15')
        else:
            if board_count > 8:
                board_count = 8
                print('Warning! T15 patch!')
            laser['ave']['pre_std'] /= board_count
            laser['ave']['int'] /= board_count
            #laser['ave']['int_len'] /= board_count
            laser['ave']['int_len'] = math.ceil(self.config['common']['integrationTime'] / self.time_step)
            for board_ind in self.boards:
                if 'captured_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['captured_bad']:
                    continue
                if laser['boards'][board_ind]['pre_std'] > self.laser_prehistory_residual_pc:
                    error = 'too large prehistory error'
                if math.fabs(laser['ave']['int'] - laser['boards'][board_ind]['int']) / \
                        laser['ave']['int'] > self.laser_integral_residual_pc:
                    print('\n')
                    for board_ind in self.boards:
                        print(board_ind, self.data[board_ind][event_ind]['t'], laser['ave']['int'], laser['boards'][board_ind]['int'])
                    if board_ind != 8:
                        '''
                        for board_ind in range(len(self.config['adc']['sync'])):
                            print(self.data[board_ind][event_ind]['t'])
                        print('\n')
                        '''
                        #fuck
                        error = 'integrals differ'
                    else:
                        print('Warning! T15 patch!', "???")
        if error is not None:
            print(error, event_ind)
        return laser, error

    def process_poly_event(self, event_ind, poly, laser):
        res = {
            'ch': []
        }
        for ch_ind in range(len(poly['channels'])):
            error = None

            if self.version >= 6:
                sp_ch = poly['channels'][ch_ind]['fast'][0]
            else:
                sp_ch = poly['channels'][ch_ind]

            board_ind = sp_ch['adc']

            if 'skip' in sp_ch and sp_ch['skip']:
                res['ch'].append({
                    'error': 'skip'
                })
                continue
            adc_gr, adc_ch = self.ch_to_gr(sp_ch['ch'])
            if self.version <= 1:
                signal = self.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
            elif self.version >= 3:
                signal = [self.header['boards'][board_ind]['offset'] - 1250 + v * 2500 / 4096 for v in self.data[board_ind][event_ind]['ch'][sp_ch['ch']]]
            else:
                signal = self.data[board_ind][event_ind]['ch'][sp_ch['ch']]
            integration_from = math.floor(laser['boards'][board_ind]['sync_ind'] +
                                          (poly['delay'] + self.config['common']['ch_delay'] * ch_ind) / self.time_step)
            integration_to = integration_from + math.ceil(self.config['common']['integrationTime'] / self.time_step)
            if integration_from < self.left_limit:
                error = 'left boundary'
            if self.version < 6:
                if integration_to > self.header['eventLength'] - self.right_limit:
                    error = 'right boundary'
            else:
                if integration_to > 1024 - self.right_limit:
                    print('warning')
                    error = 'right boundary'
            zero = statistics.fmean(signal[:integration_from])

            maximum = float('-inf')
            minimum = float('inf')
            for cell in signal:
                maximum = max(maximum, cell)
                minimum = min(minimum, cell)
            if minimum - self.offscale_threshold < self.header['boards'][board_ind]['offset'] - self.adc_baseline:
                #error = 'minimum %.1f, index = %d, poly = %d, ch = %d' % (minimum, event_ind, poly['ind'], ch_ind + 1)
                error = 'minimum %.1f, index = %d, poly = %d, ch = %d' % (minimum, event_ind, 99, ch_ind + 1)
            elif maximum + self.offscale_threshold > self.header['boards'][board_ind]['offset'] + self.adc_baseline:
                #error = 'maximum %.1f, index = %d, poly = %d, ch = %d' % (minimum, event_ind, poly['ind'], ch_ind + 1)
                error = 'maximum %.1f, index = %d, poly = %d, ch = %d' % (minimum, event_ind, 99, ch_ind + 1)

            integral = 0
            if error is None:
                for cell in range(integration_from, integration_to - 1):
                    integral += self.time_step * (signal[cell] + signal[cell + 1] - 2 * zero) * 0.5  # ns*mV
            else:
                print(error)

            if self.version < 6:
                if 'matchingFastGain' not in self.config['preamp']:
                    matching_gain = 1
                    print('WARNING! forgotten preamp gain')
                    #fuck
                else:
                    matching_gain = self.config['preamp']['matchingFastGain']
                photoelectrons = integral * 1e-3 * 1e-9 / (self.config['preamp']['apdGain'] *
                                                           phys_const.q_e *
                                                           self.config['preamp']['feedbackResistance'] *
                                                           sp_ch['fast_gain'] *
                                                           matching_gain)
                if self.config['preamp']['voltageDivider']:
                    photoelectrons *= 2
                pre_std = statistics.stdev(signal[:integration_from], zero)
                err2 = math.pow(pre_std * matching_gain * 4 / sp_ch['fast_gain'], 2) * 6715 * 0.0625 - 1.14e4 * 0.0625

            else:
                matching_gain = self.config['preamp'][poly['channels'][ch_ind]['preamp']]['matchingFastGain']
                photoelectrons = integral * 1e-3 * 1e-9 / (self.config['preamp'][poly['channels'][ch_ind]['preamp']]['apdGain'] *
                                                           phys_const.q_e *
                                                           self.config['preamp'][poly['channels'][ch_ind]['preamp']]['feedbackResistance'] *
                                                           sp_ch['gain'] *
                                                           matching_gain)
                pre_std = statistics.stdev(signal[:integration_from], zero) * 1e-1 * 10 / sp_ch['gain']
                if self.config['preamp'][poly['channels'][ch_ind]['preamp']]['voltageDivider']:
                    photoelectrons *= 2
                    pre_std *= 2
                err2 = math.pow(pre_std*2, 2) * 6715 * 0.0625 - 1.14e4 * 0.0625

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
