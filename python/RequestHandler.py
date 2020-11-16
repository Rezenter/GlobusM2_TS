import os
import python.process.rawToSignals as raw_proc


def __init__():
    return


DB_PATH = 'd:/data/GTS-Core-2020/db/'
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
            'adc': {},
            'laser': {},
            'view': {
                'refresh': self.refresh_shots,
                'get_shot': self.get_shot,
                'get_event': self.get_event
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
        shot_path = '%s%s' % (path, req['shotn'])
        if not os.path.isdir(shot_path):
            resp['ok'] = False
            resp['description'] = 'Requested shotn is missing.'
            return resp
        if not os.path.isfile('%s/%s.%s' % (shot_path, HEADER_FILE, FILE_EXT)):
            resp['ok'] = False
            resp['description'] = 'Requested shot is missing header file.'
            return resp
        if self.raw_processor is None or self.raw_processor.shotn != req['shotn']:
            self.raw_processor = raw_proc.Integrator(DB_PATH, req['shotn'], req['is_plasma'], '2020.11.12')
        resp = {
            'header': {},
            'timestamps': [],
            'energies': [],
            'polys': [],
            'sizes': []
        }

        resp['ok'] = True
        return resp

    def get_event(self, req):
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
        shot_path = '%s%s' % (path, req['shotn'])
        if not os.path.isdir(shot_path):
            resp['ok'] = False
            resp['description'] = 'Requested shotn is missing.'
            return resp
        if 'board' not in req:
            resp['ok'] = False
            resp['description'] = '"board" field is missing from request.'
            return resp
        board_id = req['board']
        if not os.path.isfile('%s/%d.%s' % (shot_path, board_id, FILE_EXT)):
            resp['ok'] = False
            resp['description'] = 'Requested shot is missing requested board file.'
            return resp
        if 'event' not in req:
            resp['ok'] = False
            resp['description'] = '"event" field is missing from request.'
            return resp
        resp['ok'] = True
        return resp
