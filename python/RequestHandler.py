import os
import time
import python.process.rawToSignals as raw_proc
import python.process.signalsToResult as fine_proc
import python.subsyst.fastADC as caen
import python.subsyst.laser1064 as laser1064
import python.utils.reconstruction.CurrentCoils as ccm


def __init__():
    return


DB_PATH = 'd:/data/db/'
PLASMA_SHOTS = 'plasma/'
DEBUG_SHOTS = 'debug/'
CONFIG = 'config/'
SPECTRAL_CAL = 'calibration/spectral/'
ABS_CAL = 'calibration/abs/processed/'
#EXPECTED_FOLDER = 'calibration/expected/'
RAW_FOLDER = 'raw/'
HEADER_FILE = 'header'
FILE_EXT = 'json'

SHOTN_FILE = 'Z:/SHOTN.TXT'

DT = 0.000005  # ms
TOLERANCE_BETWEEN_SAMLONGS = DT * 10
TOLERANCE_BETWEEN_BOARDS = 0.05  # ms


class Handler:

    def __init__(self):
        self.HandlingTable = {
            'adc': {
                'status': self.fast_status,
                'arm': self.fast_arm,
                'disarm': self.fast_disarm
            },
            'laser': {
                'connect': self.las_connect,
                'status': self.las_status,
                'fire': self.las_fire,
                'idle': self.las_idle
            },
            'view': {
                'refresh': self.refresh_shots,
                'get_shot': self.get_shot,
                'get_event_sig': self.get_event_sig,
                'get_event_raw': self.get_event_raw,
                'get_expected': self.get_expected,
                'save_shot': self.save_shot,
                'export_shot': self.export_shot,
                'chord_int': self.get_chord_integrals
            }
        }
        self.plasma_path = '%s%s' % (DB_PATH, PLASMA_SHOTS)
        self.debug_path = '%s%s' % (DB_PATH, DEBUG_SHOTS)
        self.config_path = '%s%s' % (DB_PATH, CONFIG)
        self.spectral_path = '%s%s' % (DB_PATH, SPECTRAL_CAL)
        self.abs_path = '%s%s' % (DB_PATH, ABS_CAL)
        self.raw_processor = None
        self.fine_processor = None
        self.las = laser1064.Chatter()
        return

    def handle_request(self, req):
        subsystem = req['subsystem']
        if subsystem not in self.HandlingTable:
            return {'ok': False, 'description': 'Subsystem is not listed.'}
        reqtype = req['reqtype']
        if reqtype in self.HandlingTable[subsystem]:
            return self.HandlingTable[subsystem][reqtype](req)
        else:
            return {'ok': False, 'description': 'Reqtype is not listed.'}

    def refresh_shots(self, req):
        resp = {}
        if not os.path.isdir(self.plasma_path + RAW_FOLDER):
            resp['ok'] = False
            resp['description'] = 'Directory for plasma shots "%s" does not exist.' % (self.plasma_path + RAW_FOLDER)
            return resp
        if not os.path.isdir(self.debug_path + RAW_FOLDER):
            resp['ok'] = False
            resp['description'] = 'Directory for debug shots "%s" does not exist.' % (self.debug_path + RAW_FOLDER)
            return resp
        resp['plasma'] = sorted(os.listdir(self.plasma_path + RAW_FOLDER), reverse=True)
        resp['debug'] = sorted(os.listdir(self.debug_path + RAW_FOLDER), reverse=True)

        tmp = sorted(os.listdir(self.config_path), reverse=True)
        resp['config'] = []
        for entry in tmp:
            if entry.endswith('.json'):
                resp['config'].append(entry[:-5])

        tmp = sorted(os.listdir(self.spectral_path), reverse=True)
        resp['spectral_cal'] = []
        for entry in tmp:
            if entry.endswith('.json'):
                resp['spectral_cal'].append(entry[:-5])

        tmp = sorted(os.listdir(self.abs_path), reverse=True)
        resp['abs_cal'] = []
        for entry in tmp:
            if entry.endswith('.json'):
                resp['abs_cal'].append(entry[:-5])
        resp['ok'] = True
        return resp

    def get_expected(self, req):
        expected = self.fine_processor.expected
        expected['ok'] = True
        resp = expected
        return resp

    def get_shot(self, req):
        resp = {}
        if 'is_plasma' not in req:
            resp['ok'] = False
            resp['description'] = '"is-plasma" field is missing from request.'
            return resp
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        if 'config' not in req:
            resp['ok'] = False
            resp['description'] = '"config" field is missing from request.'
            return resp
        if self.fine_processor is None or self.fine_processor.shotn != req['shotn']:
            self.fine_processor = fine_proc.Processor(DB_PATH, int(req['shotn']), req['is_plasma'], '2021.02.01',
                                                      '2021.02.03')
            if self.fine_processor.get_error() is not None:
                self.get_integrals_shot(req)
                self.fine_processor.load()
        resp = self.fine_processor.get_data()
        if self.raw_processor is None or self.raw_processor.is_plasma != req['is_plasma'] or \
                self.raw_processor.shotn != int(req['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], req['config'])
        resp['header'] = self.raw_processor.header
        resp['ok'] = True
        return resp

    def save_shot(self, req):
        if 'is_plasma' not in req:
            return {
                'ok': False,
                'description': '"is-plasma" field is missing from request.'
            }
        if 'shotn' not in req:
            return {
                'ok': False,
                'description': '"shotn" field is missing from request.'
            }
        if 'events' not in req:
            return {
                'ok': False,
                'description': '"events" field is missing from request.'
            }
        if self.fine_processor is None or self.fine_processor.shotn != req['shotn']:
            self.fine_processor = fine_proc.Processor(DB_PATH, int(req['shotn']), req['is_plasma'], '2021.02.01',
                                                      '2021.02.03')
            err = self.fine_processor.get_error()
            if err is not None:
                return {
                    'ok': False,
                    'description': err
                }
        ok = self.fine_processor.update_events(req['events'])
        if ok:
            return {
                'ok': True
            }
        else:
            return {
                'ok': False,
                'descrioption': self.fine_processor.get_error()
            }

    def export_shot(self, req):
        if 'is_plasma' not in req:
            return {
                'ok': False,
                'description': '"is-plasma" field is missing from request.'
            }
        if 'shotn' not in req:
            return {
                'ok': False,
                'description': '"shotn" field is missing from request.'
            }
        if 'from' not in req:
            return {
                'ok': False,
                'description': '"from" field is missing from request.'
            }
        if 'to' not in req:
            return {
                'ok': False,
                'description': '"to" field is missing from request.'
            }
        if 'correction' not in req:
            return {
                'ok': False,
                'description': '"correction" field is missing from request.'
            }
        print('\n\n\ncorrection = ', float(req['correction']), '\n\n\n')
        if self.fine_processor is None or self.fine_processor.shotn != req['shotn']:
            self.fine_processor = fine_proc.Processor(DB_PATH, int(req['shotn']), req['is_plasma'], '2021.02.01',
                                                      '2021.02.03')
            err = self.fine_processor.get_error()
            if err is not None:
                return {
                    'ok': False,
                    'description': err
                }
        return self.fine_processor.to_csv(req['from'], req['to'], float(req['correction']))

    def get_chord_integrals(self, req):
        resp = {}
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        if 'r' not in req:
            resp['ok'] = False
            resp['description'] = '"r" field is missing from request.'
            return resp
        if 'start' not in req:
            resp['ok'] = False
            resp['description'] = '"start" field is missing from request.'
            return resp
        if 'stop' not in req:
            resp['ok'] = False
            resp['description'] = '"start" field is missing from request.'
            return resp

        if self.fine_processor is None or self.fine_processor.shotn != req['shotn']:
            self.fine_processor = fine_proc.Processor(DB_PATH, int(req['shotn']), True, '2021.02.01',
                                                      '2021.02.03')
            if self.fine_processor.get_error() is not None:
                self.get_integrals_shot(req)
                self.fine_processor.load()
        return ccm.get_integrals(int(req['shotn']),
                                 self.fine_processor.get_data(),
                                 float(req['r']),
                                 float(req['start']),
                                 float(req['stop']))

    def get_integrals_shot(self, req):
        resp = {}
        if 'is_plasma' not in req:
            resp['ok'] = False
            resp['description'] = '"is-plasma" field is missing from request.'
            return resp
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        if req['is_plasma']:
            path = self.plasma_path
        else:
            path = self.debug_path
        shot_path = '%s%s%s' % (path, RAW_FOLDER, req['shotn'])
        if not os.path.isdir(shot_path):
            resp['ok'] = False
            print(shot_path)
            resp['description'] = 'Requested shotn is missing.'
            return resp
        if 'config' not in req:
            resp['ok'] = False
            resp['description'] = '"config" field is missing from request.'
            return resp
        if self.raw_processor is None or self.raw_processor.is_plasma != req['is_plasma'] or \
                self.raw_processor.shotn != int(req['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], req['config'])
        resp = {
            'timestamps': [],
            'energies': [],
            'polys': [poly for poly in self.raw_processor.config['poly']]
        }
        for event_ind in range(len(self.raw_processor.processed)):
            event = self.raw_processor.processed[event_ind]
            resp['timestamps'].append(event['timestamp'])
            resp['energies'].append(event['laser']['ave']['int'])
        resp['ok'] = True
        return resp

    def get_event_sig(self, req):
        resp = {}
        if 'event' not in req:
            resp['ok'] = False
            resp['description'] = '"event" field is missing from request.'
            return resp
        if 'is_plasma' not in req:
            resp['ok'] = False
            resp['description'] = '"is-plasma" field is missing from request.'
            return resp
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        if req['is_plasma']:
            path = self.plasma_path
        else:
            path = self.debug_path
        shot_path = '%s%s%s' % (path, RAW_FOLDER, req['shotn'])
        if not os.path.isdir(shot_path):
            resp['ok'] = False
            resp['description'] = 'Requested shotn is missing.'
            return resp
        if self.raw_processor is None or self.raw_processor.is_plasma != req['is_plasma'] or \
                self.raw_processor.shotn != int(req['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], '2020.11.27')
        resp = self.raw_processor.processed[req['event']]
        resp['ok'] = True
        return resp

    def get_event_raw(self, req):
        resp = {}
        if 'event' not in req:
            resp['ok'] = False
            resp['description'] = '"event" field is missing from request.'
            return resp
        if 'is_plasma' not in req:
            resp['ok'] = False
            resp['description'] = '"is-plasma" field is missing from request.'
            return resp
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        if req['is_plasma']:
            path = self.plasma_path
        else:
            path = self.debug_path
        shot_path = '%s%s%s' % (path, RAW_FOLDER, req['shotn'])
        if not os.path.isdir(shot_path):
            resp['ok'] = False
            resp['description'] = 'Requested shotn is missing.'
            return resp
        if 'config' not in req:
            resp['ok'] = False
            resp['description'] = '"config" field is missing from request.'
            return resp
        if self.raw_processor is None or self.raw_processor.is_plasma != req['is_plasma'] or \
                self.raw_processor.shotn != int(req['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], req['config'])
        if 'poly' not in req:
            resp['ok'] = False
            resp['description'] = '"poly" field is missing from request.'
            return resp
        if not self.raw_processor.loaded:
            self.raw_processor.load_raw()
        event = []
        starts = []
        for ch in self.raw_processor.config['poly'][int(req['poly'])]['channels']:
            adc_gr, adc_ch = self.raw_processor.ch_to_gr(ch['ch'])
            event.append(self.raw_processor.data[ch['adc']][int(req['event'])][adc_gr]['data'][adc_ch])
            starts.append(self.raw_processor.processed[int(req['event'])]['laser']['boards'][ch['adc']]['sync_ind'])
        adc_gr, adc_ch = self.raw_processor.ch_to_gr(self.raw_processor.config['adc']['sync'][ch['adc']]['ch'])
        resp = {
            'data': event,
            'laser': self.raw_processor.data[ch['adc']][int(req['event'])][adc_gr]['data'][adc_ch],
            'starts': starts,
            'laser_start': self.raw_processor.processed[int(req['event'])]['laser']['boards'][ch['adc']]['sync_ind'],
            'ok': True
        }
        return resp

    def fast_status(self, req):
        print('status...')
        if not os.path.isfile(SHOTN_FILE):
            return {
                'ok': False,
                'description': 'Shotn file not found.'
            }
        try:
            caen.connect()
        except ConnectionError as err:
            print('caen connection error', err)
            return {
                'ok': False,
                'description': ('Connection error: "%s"' % err)
            }
        caen.send_cmd(caen.Commands.Alive)
        time.sleep(1)
        resp = caen.read()
        print(resp)
        caen.disconnect()
        if resp['status']:
            shotn = 0
            with open(SHOTN_FILE, 'r') as shotn_file:
                line = shotn_file.readline()
                shotn = int(line)
            return {
                'ok': True,
                'resp': resp,
                'shotn': shotn
            }
        else:
            return resp

    def fast_arm(self, req):
        if 'isPlasma' not in req:
            return {
                'ok': False,
                'description': '"isPlasma" field is missing from request.'
            }

        shot_filename = "%s%sSHOTN.TXT" % (DB_PATH, DEBUG_SHOTS)
        isPlasma = req['isPlasma']
        if isPlasma:
            shot_filename = SHOTN_FILE
        if not os.path.isfile(shot_filename):
            return {
                'ok': False,
                'description': 'Shotn file "%s" not found.' %shot_filename
            }
        shotn = 0
        with open(shot_filename, 'r') as shotn_file:
            line = shotn_file.readline()
            shotn = int(line)

        try:
            caen.connect()
        except ConnectionError as err:
            print('caen connection error', err)
            return {
                'ok': False,
                'description': ('Connection error: "%s"' % err)
            }

        caen.send_cmd(caen.Commands.Arm, [shotn, isPlasma])
        print(caen.read())

        caen.disconnect()

        if not isPlasma:
            with open(shot_filename, 'w') as shotn_file:
                #shotn_file.seek(0)
                shotn_file.write('%d' % (shotn + 1))

        return {
            'ok': True,
            'shotn': shotn
        }

    def fast_disarm(self, req):
        try:
            caen.connect()
        except ConnectionError as err:
            print('caen connection error', err)
            return {
                'ok': False,
                'description': ('Connection error: "%s"' % err)
            }

        caen.send_cmd(caen.Commands.Disarm)
        caen.read()

        time.sleep(0.5)
        caen.disconnect()
        return {
            'ok': True
        }

    def las_connect(self, req):
        return self.las.connect()

    def las_status(self, req):
        return self.las.status()

    def las_fire(self, req):
        return self.las.set_state_3()

    def las_idle(self, req):
        return self.las.set_state_1()
