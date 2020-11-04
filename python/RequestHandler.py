import os
import ijson
import math
import itertools

def __init__():
    return


DB_PATH = 'd:/data/fastDump/'
PLASMA_SHOTS = 'plasma/'
DEBUG_SHOTS = 'debug/'
HEADER_FILE = 'header'
FILE_EXT = 'json'
DT = 0.000005  # ms
TOLERANCE_BETWEEN_SAMLONGS = DT * 10
TOLERANCE_BETWEEN_BOARDS = 0.05  # ms


class Handler:

    def __init__(self):
        self.HandlingTable = {
            'adc': {},
            'view': {
                'refresh': self.refresh_shots,
                'get_shot': self.get_shot,
                'get_event': self.get_event
            }
        }
        self.plasma_path = '%s%s' % (DB_PATH, PLASMA_SHOTS)
        self.debug_path = '%s%s' % (DB_PATH, DEBUG_SHOTS)
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
        if not os.path.isdir(self.plasma_path):
            resp['ok'] = False
            resp['description'] = 'Directory for plasma shots "%s" does not exist.' % self.plasma_path
            return resp
        if not os.path.isdir(self.debug_path):
            resp['ok'] = False
            resp['description'] = 'Directory for debug shots "%s" does not exist.' % self.debug_path
            return resp
        resp['plasma'] = sorted(os.listdir(self.plasma_path), reverse=True)
        resp['debug'] = sorted(os.listdir(self.debug_path), reverse=True)
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
        resp = {
            'header': {},
            'boards': [[] for board in range(4)],
            'sus_boards': [],
            'sus_events': []
        }
        with open('%s/%s.%s' % (shot_path, HEADER_FILE, FILE_EXT), 'rb') as header_file:
            header = ijson.kvitems(header_file, '', use_float=True)
            for key, value in header:
                resp['header'][key] = value
        for board_id in range(4):
            if os.path.isfile('%s/%d.%s' % (shot_path, board_id, FILE_EXT)):
                with open('%s/%d.%s' % (shot_path, board_id, FILE_EXT), 'rb') as board_file:
                    print('opened %d' % board_id)
                    events = ijson.basic_parse(board_file, use_float=True)
                    counter = 0
                    current = 0
                    for event, value in events:
                        if event == 'map_key' and value == 'timestamp':
                            event, value = events.__next__()
                            if not counter:
                                resp['boards'][board_id].append(value)
                                current = value
                            else:
                                if len(resp['boards'][board_id]) > 1 and \
                                        not math.isclose(value, current, abs_tol=TOLERANCE_BETWEEN_SAMLONGS):
                                    resp['sus_boards'].append({
                                        'board': board_id,
                                        'event': len(resp['boards'][board_id]) - 1,
                                        'group': counter,
                                        'delta': current - value
                                    })
                                if counter == 7:
                                    counter = 0
                                    continue
                            counter += 1
        min_events = min(len(resp['boards'][0]), len(resp['boards'][1]), len(resp['boards'][2]), len(resp['boards'][3]))
        for ev_id in range(min_events):
            if math.isclose(resp['boards'][0][ev_id], resp['boards'][1][ev_id],
                                abs_tol=TOLERANCE_BETWEEN_BOARDS):
                if math.isclose(resp['boards'][0][ev_id], resp['boards'][2][ev_id],
                                abs_tol=TOLERANCE_BETWEEN_BOARDS):
                    if math.isclose(resp['boards'][0][ev_id], resp['boards'][3][ev_id],
                                    abs_tol=TOLERANCE_BETWEEN_BOARDS):
                        continue
            resp['sus_events'].append({
                'event': ev_id,
                'timestamps': [
                    resp['boards'][0][ev_id],
                    resp['boards'][1][ev_id],
                    resp['boards'][2][ev_id],
                    resp['boards'][3][ev_id]
                ]
            })
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
        with open('%s/%d.%s' % (shot_path, board_id, FILE_EXT), 'rb') as board_file:
            objects = ijson.items(board_file, 'item', use_float=True)
            resp['event'] = next(itertools.islice(objects, req['event'], req['event'] + 1))
        resp['ok'] = True
        return resp
