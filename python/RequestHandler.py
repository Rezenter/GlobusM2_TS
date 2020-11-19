import os
import python.process.rawToSignals as raw_proc
import python.subsyst.fastADC as caen
import time


def __init__():
    return


DB_PATH = 'd:/data/db/'
PLASMA_SHOTS = 'plasma/'
DEBUG_SHOTS = 'debug/'
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
                'arm': self.fast_arm
            },
            'laser': {},
            'view': {
                'refresh': self.refresh_shots,
                'get_shot': self.get_shot,
                'get_event_sig': self.get_event_sig
            }
        }
        self.plasma_path = '%s%s' % (DB_PATH, PLASMA_SHOTS)
        self.debug_path = '%s%s' % (DB_PATH, DEBUG_SHOTS)
        self.raw_processor = None
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
        if self.raw_processor is None or self.raw_processor.shotn != req['shotn']:
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shotn']), req['is_plasma'], '2020.11.12')
        resp = {
            'timestamps': [],
            'energies': [],
            'polys': [poly for poly in self.raw_processor.config['poly']]
        }
        for event_ind in range(len(self.raw_processor.processed)):
            event = self.raw_processor.processed[event_ind]
            resp['timestamps'].append(event_ind * 3.03030303)
            resp['energies'].append(event['laser']['ave']['int'])
        resp['ok'] = True
        return resp

    def get_event_sig(self, req):
        resp = {}
        if 'event' not in req:
            resp['ok'] = False
            resp['description'] = '"event" field is missing from request.'
            return resp
        resp = self.raw_processor.processed[req['event']]
        resp['ok'] = True
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

        caen.send_cmd(caen.Commands.Alive)
        print(caen.read())

        time.sleep(0.1)

        caen.send_cmd(caen.Commands.Arm, [shotn, isPlasma])
        print(caen.read())

        caen.disconnect()

        with open(shot_filename, 'w') as shotn_file:
            shotn_file.seek(0)
            shotn += 1
            shotn_file.write('%d' % shotn)

        resp['ok'] = True
        return resp
