import os
import python.process.rawToSignals as raw_proc
import python.process.signalsToResult as fine_proc
import python.subsyst.fastADC as caen
import ijson


def __init__():
    return


DB_PATH = 'd:/data/db/'
PLASMA_SHOTS = 'plasma/'
DEBUG_SHOTS = 'debug/'
EXPECTED_FOLDER = 'calibration/expected/'
RAW_FOLDER = 'raw/'
HEADER_FILE = 'header'
FILE_EXT = 'json'

DT = 0.000005  # ms
TOLERANCE_BETWEEN_SAMLONGS = DT * 10
TOLERANCE_BETWEEN_BOARDS = 0.05  # ms


class Handler:

    def __init__(self):
        self.HandlingTable = {
            'adc': {
                'arm': self.fast_arm,
                'disarm': self.fast_disarm
            },
            'laser': {},
            'view': {
                'refresh': self.refresh_shots,
                'get_shot': self.get_shot,
                'get_event_sig': self.get_event_sig,
                'get_event_raw': self.get_event_raw,
                'get_expected': self.get_expected
            }
        }
        self.plasma_path = '%s%s' % (DB_PATH, PLASMA_SHOTS)
        self.debug_path = '%s%s' % (DB_PATH, DEBUG_SHOTS)
        self.raw_processor = None
        self.fine_processor = None
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
        if self.fine_processor is None or self.fine_processor.shotn != req['shotn']:
            self.fine_processor = fine_proc.Processor(DB_PATH, int(req['shotn']), req['is_plasma'], '2020.11.25',
                                                      '2020.11.06')
            if self.fine_processor.get_error() is not None:
                self.get_integrals_shot(req)
                self.fine_processor.load()
        resp = self.fine_processor.get_data()
        if self.raw_processor is None or self.raw_processor.is_plasma != req['is_plasma'] or \
                self.raw_processor.shotn != int(req['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], '2020.11.27')
        resp['header'] = self.raw_processor.header
        resp['ok'] = True
        return resp

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
        if self.raw_processor is None or self.raw_processor.is_plasma != req['is_plasma'] or \
                self.raw_processor.shotn != int(req['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], '2020.11.27')
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
        if self.raw_processor is None or self.raw_processor.is_plasma != req['is_plasma'] or \
                self.raw_processor.shotn != int(req['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], '2020.11.27')
        if 'poly' not in req:
            resp['ok'] = False
            resp['description'] = '"poly" field is missing from request.'
            return resp
        if not self.raw_processor.loaded:
            self.raw_processor.load_raw()
        event = []
        for ch in self.raw_processor.config['poly'][int(req['poly'])]['channels']:
            adc_gr, adc_ch = self.raw_processor.ch_to_gr(ch['ch'])
            event.append(self.raw_processor.data[ch['adc']][int(req['event'])][adc_gr]['data'][adc_ch])
        adc_gr, adc_ch = self.raw_processor.ch_to_gr(self.raw_processor.config['adc']['sync'][ch['adc']]['ch'])
        resp = {
            'data': event,
            'laser': self.raw_processor.data[ch['adc']][int(req['event'])][adc_gr]['data'][adc_ch],
            'ok': True
        }
        return resp

    def fast_arm(self, req):
        resp = {}
        if 'isPlasma' not in req:
            resp['ok'] = False
            resp['description'] = '"isPlasma" field is missing from request.'
            return resp

        shot_filename = "%s/shotn.txt" % DB_PATH
        isPlasma = req['isPlasma']
        shotn = 0
        with open(shot_filename, 'r') as shotn_file:
            line = shotn_file.readline()
            shotn = int(line)

        caen.connect()

        caen.send_cmd(caen.Commands.Arm, [shotn, isPlasma])
        print(caen.read())

        caen.disconnect()

        with open(shot_filename, 'w') as shotn_file:
            shotn_file.seek(0)
            shotn += 1
            shotn_file.write('%d' % shotn)

        resp['ok'] = True
        return resp

    def fast_disarm(self, req):
        resp = {}

        caen.connect()
        caen.send_cmd(caen.Commands.Disarm)
        print(caen.read())
        caen.disconnect()

        resp['ok'] = True
        return resp
