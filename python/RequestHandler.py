import json
import os
import logging
import time
import requests
import ijson
import math
import shtRipper
from pathlib import Path
import shutil

import python.process.rawToSignals as raw_proc
import python.process.signalsToResult as fine_proc
import python.subsyst.fastADC as caen
import python.subsyst.laser1064 as laser1064
import python.subsyst.db as db
import python.subsyst.tokamak as tokamak
#import python.subsyst.crate as crate
import python.utils.reconstruction.CurrentCoils as ccm
import python.utils.reconstruction.stored_energy as ccm_energy
import python.utils.sht.sht_viewer as sht
from python.subsyst.slowADC import SlowADC

DB_PATH = 'd:/data/db/'
PLASMA_SHOTS = 'plasma/'
DEBUG_SHOTS = 'debug/'
CONFIG = 'config/'
SPECTRAL_CAL = 'calibration/expected/'
ABS_CAL = 'calibration/abs/processed/'
EXPECTED_FOLDER = 'calibration/expected/'
RAW_FOLDER = 'raw/'
RES_FOLDER = 'result/'
SLOW_RAW_FOLDER = 'slow/raw/'
HEADER_FILE = 'header'
FILE_EXT = 'json'
GUI_CONFIG = 'config/'
#CFM_ADDR = 'http://172.16.12.87:8050/_dash-update-component'
CFM_ADDR = 'http://172.16.12.150:8050/_dash-update-component'
CFM_DB = 'y:/!!!CURRENT_COIL_METHOD/old_mcc/'  # y = \\172.16.12.127
CFM_DB_NEW = 'y:/!!!CURRENT_COIL_METHOD/V3_zad7_mcc/'  # y = \\172.16.12.127
PUB_PATH = 'Y:/!!!TS_RESULTS/2022/'

SHOTN_FILE = 'Z:/SHOTN.TXT'  # 192.168.101.24
#SHOTN_FILE = 'W:/SHOTN.TXT'  # 172.16.12.127/Data

DT = 0.000005  # ms
TOLERANCE_BETWEEN_SAMLONGS = DT * 10
TOLERANCE_BETWEEN_BOARDS = 0.05  # ms

laser_maxTime = 60 + 10  # seconds
format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")


def authenticate(req):
    if 'pass' not in req or req['pass'] != '******':
        return {'ok': False}
    return {'ok': True}


class Handler:
    def __init__(self):
        self.HandlingTable = {
            'diag': {
                'arm': self.arm_all,
                'status': self.diag_status,
                'get_conf': self.get_configs,
                'auth': authenticate
            },
            'slow_adc': {
                'status': self.slow_status,
                'arm': self.slow_arm,
                'disarm': self.slow_disarm
            },
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
                'load_version': self.get_version,
                'get_shot': self.get_shot,
                'get_event_sig': self.get_event_sig,
                'get_event_raw': self.get_event_raw,
                'get_expected': self.get_expected,
                'save_shot': self.save_shot,
                'export_shot': self.export_shot,
                'chord_int': self.get_chord_integrals,
                'load_ccm': self.load_ccm,
                'load_sht': self.sht_names,
                'get_sht_signal': self.sht_signal,
                'calc_cfm': self.calc_cfm
            },
            'db': {
                'get_shot': self.get_db_shot,
                'get_shot_verified': self.get_db_shot_ver
            }
        }
        self.plasma_path = '%s%s' % (DB_PATH, PLASMA_SHOTS)
        self.debug_path = '%s%s' % (DB_PATH, DEBUG_SHOTS)
        self.config_path = '%s%s' % (DB_PATH, CONFIG)
        self.spectral_path = '%s%s' % (DB_PATH, SPECTRAL_CAL)
        self.abs_path = '%s%s' % (DB_PATH, ABS_CAL)
        self.plasma_verified_path = '%s%s/' % (self.plasma_path, 'verified')
        self.raw_processor = None
        self.fine_processor = None
        self.sht = None
        self.las = laser1064.ControlUnit()
        self.state = {}
        self.slow = None

        print('connecting udp...')
        self.tokamak = tokamak.Sync(self.diag_disarm)
        print('connecting coolant...')
        self.las_cool = laser1064.Coolant()
        #print('connecting crate...')
        #self.crate = crate.Crate()
        print('DONE')
        self.db = db.DB(self.plasma_path)
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

        #resp['plasma'] = sorted(os.listdir(self.plasma_path + RAW_FOLDER), reverse=True)
        #resp['processed'] = sorted(os.listdir(self.plasma_path + RES_FOLDER), reverse=True)

        if 'debug' in req:
            resp['debug'] = sorted(os.listdir(self.debug_path + RAW_FOLDER), reverse=True)
        else:
            resp['plasma'] = []
            for shotn in sorted(os.listdir(self.plasma_path + RAW_FOLDER), reverse=True):
                entry = {
                    '#': shotn,
                }
                result_folder = '%s%s/' % (self.plasma_verified_path, shotn)
                if os.path.isdir(result_folder):
                    versions = sorted([name for name in os.listdir(result_folder) if os.path.isdir(os.path.join(result_folder, name))], reverse=True)
                    entry['versions'] = []
                    for ver in versions:
                        with open('%s%s/result.json' % (result_folder, ver), 'r') as file:
                            res = json.load(file)
                            entry['versions'].append({
                                'ver': ver,
                                'rating': 0,
                                'comment': '',
                                'config': res['config_name'],
                                'abs_cal': res['absolute_name'],
                                'sp_cal': res['spectral_name']
                            })
                    #load header of each entry

                    with open('%sdefault.txt' % result_folder, 'r') as file:
                        entry['default_version'] = 'v%02d' % int(file.readline())
                with open(self.plasma_path + RAW_FOLDER + shotn + '/header.json', 'r') as file:
                    header = json.load(file)
                    if 'aux' in header:
                        entry['default_configs'] = header['aux']

                resp['plasma'].append(entry)

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
        if 'shot' not in req:
            return {
                'ok': False,
                'description': '"shot" field is missing from request'
            }

        expected_full_name = '%s%s%s.%s' % (DB_PATH, EXPECTED_FOLDER, req['shot']['spectral_name'], FILE_EXT)
        expected = {}
        with open(expected_full_name, 'r') as expected_file:
            obj = ijson.kvitems(expected_file, '', use_float=True)
            for k, v in obj:
                expected[k] = v
        expected['modification'] = os.path.getmtime(expected_full_name)

        expected['ok'] = True
        resp = expected
        return resp

    def get_shot(self, req):
        self.raw_processor = None
        self.fine_processor = None
        self.sht = None
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
        if 'abs_cal' not in req:
            resp['ok'] = False
            resp['description'] = '"abs_cal" field is missing from request.'
            return resp
        if 'sp_cal' not in req:
            resp['ok'] = False
            resp['description'] = '"sp_cal" field is missing from request.'
            return resp
        if self.fine_processor is None or self.fine_processor.shotn != req['shotn']:
            self.fine_processor = fine_proc.Processor(db_path=DB_PATH,
                                                      shotn=int(req['shotn']),
                                                      is_plasma=req['is_plasma'],
                                                      expected_id=req['sp_cal'],
                                                      absolute_id=req['abs_cal'])
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

    def get_version(self, req):
        self.raw_processor = None
        self.fine_processor = None
        self.sht = None
        resp = {}
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        if 'ver' not in req:
            resp['ok'] = False
            resp['description'] = '"ver" field is missing from request.'
            return resp

        result_folder = '%s%05d/' % (self.plasma_verified_path, int(req['shotn']))
        if not os.path.isdir(result_folder):
            resp['ok'] = False
            resp['description'] = 'Verified shotn "%s" does not exist' % req['shotn']
        result_folder = '%s%s/' % (result_folder, req['ver'])
        if not os.path.isdir(result_folder):
            resp['ok'] = False
            resp['description'] = 'Verified shotn "%s" with version "%s" does not exist' % (req['shotn'], req['ver'])

        with open('%sresult.%s' % (result_folder, FILE_EXT), 'r') as file:
            resp['res'] = json.load(file)

        resp['ok'] = True
        return resp

    def save_shot(self, req):
        data = req['shot']

        if self.raw_processor is None or self.raw_processor.is_plasma != True or \
                self.raw_processor.shotn != int(data['shotn']):
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(data['shotn']), True, data['config_name'])
        if len(data['events']) != len(self.raw_processor.processed):
            return {
                'ok': False,
                'description': 'Event count differs'
            }

        result_folder = '%s%05d/' % (self.plasma_verified_path, int(data['shotn']))
        if not os.path.isdir(result_folder):
            os.mkdir(result_folder)
            req['default'] = True
        version = 1
        while os.path.isdir('%sv%02d' % (result_folder, version)):
            version += 1
        result_folder += 'v%02d/' % version
        os.mkdir(result_folder)
        data['version'] = version
        with open('%sresult.%s' % (result_folder, FILE_EXT), 'w') as out_file:
            json.dump(data, out_file, indent=1)
        req['cfm']['version'] = version
        with open('%scfm_res.%s' % (result_folder, FILE_EXT), 'w') as out_file:
            json.dump(req['cfm'], out_file, indent=1)
        if req['default']:
            with open('%s%05d/default.txt' % (self.plasma_verified_path, int(data['shotn'])), 'w') as out_file:
                out_file.write('%d' % version)

        self.raw_processor.save_processed('%ssignal.%s' % (result_folder, FILE_EXT), version)

        self.publish(req=req, result=data)
        return {
            'ok': True,
            'ver': version
        }

    def export_shot(self, req):
        if 'shot' not in req:
            return {
                'ok': False,
                'description': '"shot" field is missing from request'
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
        if 'old' not in req:
            return {
                'ok': False,
                'description': '"old" field is missing from request.'
            }

        if 'cfm' not in req:
            resp = self.to_csv(req['shot'], req['from'], req['to'])
        else:
            resp = self.to_csv(req['shot'], req['from'], req['to'], req['cfm'])
        if req['old']:
            resp['old'] = self.to_old_csv(req['shot'], req['from'], req['to'])
        return resp

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

        if 'abs_cal' not in req:
            return {
                'ok': False,
                'description': '"abs_cal" field is missing from request.'
            }
        if 'sp_cal' not in req:
            return {
                'ok': False,
                'description': '"sp_cal" field is missing from request.'
            }
        if self.fine_processor is None or self.fine_processor.shotn != req['shotn']:
            self.fine_processor = fine_proc.Processor(db_path=DB_PATH,
                                                      shotn=int(req['shotn']),
                                                      is_plasma=req['is_plasma'],
                                                      expected_id=req['sp_cal'],
                                                      absolute_id=req['abs_cal'])
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
            resp['description'] = 'Requested shotn is missing: %s.' % shot_path
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
            'energies': []
        }
        for event_ind in range(len(self.raw_processor.processed)):
            event = self.raw_processor.processed[event_ind]
            if 'timestamp' in event:
                resp['timestamps'].append(event['timestamp'])
                if 'energies' in resp and 'laser' in event:
                    resp['energies'].append(event['laser']['ave']['int'])
                else:
                    resp['energies'].append(0)
            else:
                resp['timestamps'].append(0)
                resp['energies'].append(0)
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
        if 'shot' not in req:
            return {
                'ok': False,
                'description': '"shot" field is missing from request'
            }
        if 'version' in req['shot']:
            with open('%s%s/v%02d/signal.%s' % (self.plasma_verified_path, req['shot']['shotn'], req['shot']['version'], FILE_EXT), 'r') as file:
                resp = json.load(file)['data'][req['event']]
                resp['ok'] = True
                return resp

        if self.fine_processor is None or self.fine_processor.shotn != int(req['shot']['shotn']):
            return {
                'ok': False,
                'description': 'server has another shotn loaded'
            }
        if self.fine_processor.get_data()['config_name'] != req['shot']['config_name']:
            return {
                'ok': False,
                'description': 'server has shot loaded with another config'
            }
        if self.fine_processor.get_data()['spectral_name'] != req['shot']['spectral_name']:
            return {
                'ok': False,
                'description': 'server has shot loaded with another spectral calibration'
            }
        if self.fine_processor.get_data()['absolute_name'] != req['shot']['absolute_name']:
            return {
                'ok': False,
                'description': 'server has shot loaded with another absolute calibration'
            }

        if self.raw_processor is None:
            self.raw_processor = raw_proc.Integrator(DB_PATH, self.fine_processor.shotn, True, req['shot']['config_name'])
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
        if 'shot' not in req:
            return {
                'ok': False,
                'description': '"shot" field is missing from request'
            }
        if 'poly' not in req:
            resp['ok'] = False
            resp['description'] = '"poly" field is missing from request.'
            return resp
        if 'version' not in req['shot']:
            if self.fine_processor is None or self.fine_processor.shotn != int(req['shot']['shotn']):
                return {
                    'ok': False,
                    'description': 'server has another shotn loaded'
                }
            if self.fine_processor.get_data()['config_name'] != req['shot']['config_name']:
                return {
                    'ok': False,
                    'description': 'server has shot loaded with another config'
                }
            if self.fine_processor.get_data()['spectral_name'] != req['shot']['spectral_name']:
                return {
                    'ok': False,
                    'description': 'server has shot loaded with another spectral calibration'
                }
            if self.fine_processor.get_data()['absolute_name'] != req['shot']['absolute_name']:
                return {
                    'ok': False,
                    'description': 'server has shot loaded with another absolute calibration'
                }
        else:
            self.raw_processor = None
            self.fine_processor = None
            self.sht = None
        shot_path = '%s%s%s' % (self.plasma_path, RAW_FOLDER, req['shot']['shotn'])
        if not req['is_plasma']:
            shot_path = '%s%s%s' % (self.debug_path, RAW_FOLDER, req['shot']['shotn'])
        if not os.path.isdir(shot_path):
            resp['ok'] = False
            resp['description'] = 'Requested shotn is missing: %s.' % shot_path
            return resp

        if self.raw_processor is None:
            self.raw_processor = raw_proc.Integrator(DB_PATH, int(req['shot']['shotn']), True, req['shot']['config_name'])

        if not self.raw_processor.loaded:
            self.raw_processor.load_raw()
        event = []
        starts = []

        for ch in self.raw_processor.config['poly'][int(req['poly'])]['channels']:
            if self.raw_processor.version == 1:
                adc_gr, adc_ch = self.raw_processor.ch_to_gr(ch['ch'])
                event.append(self.raw_processor.data[ch['adc']][int(req['event'])][adc_gr]['data'][adc_ch])
            else:
                event.append(list([self.raw_processor.header['offset'] - 1250 + v * 2500 / 4096] for v in self.raw_processor.data[ch['adc']][int(req['event'])]['ch'][ch['ch']]))
            starts.append(self.raw_processor.processed[int(req['event'])]['laser']['boards'][ch['adc']]['sync_ind'])

        board_ind = self.raw_processor.config['poly'][int(req['poly'])]['channels'][0]['adc']
        if self.raw_processor.version == 1:
            adc_gr, adc_ch = self.raw_processor.ch_to_gr(self.raw_processor.config['adc']['sync'][board_ind]['ch'])
            las = self.raw_processor.data[board_ind][int(req['event'])][adc_gr]['data'][adc_ch]
        else:
            las = (list([self.raw_processor.header['offset'] - 1250 + v * 2500 / 4096] for v in self.raw_processor.data[board_ind][int(req['event'])]['ch'][self.raw_processor.config['adc']['sync'][board_ind]['ch']]))
        resp = {
            'data': event,
            'laser': las,
            'starts': starts,
            'laser_start': self.raw_processor.processed[int(req['event'])]['laser']['boards'][board_ind]['sync_ind'],
            'ok': True
        }
        return resp

    def load_ccm(self, req):
        resp = {}
        if 'shot' not in req:
            return {
                'ok': False,
                'description': '"shot" field is missing from request'
            }
        if 'version' in req['shot']:
            with open('%s%s/v%02d/cfm_res.%s' % (self.plasma_verified_path, req['shot']['shotn'], req['shot']['version'], FILE_EXT), 'r') as file:
                return json.load(file)

        if 'start' not in req:
            resp['ok'] = False
            resp['description'] = '"start" field is missing from request.'
            return resp
        if 'stop' not in req:
            resp['ok'] = False
            resp['description'] = '"start" field is missing from request.'
            return resp
        if 'r' not in req:
            resp['ok'] = False
            resp['description'] = '"r" field is missing from request.'
            return resp

        if self.fine_processor is None or self.fine_processor.shotn != int(req['shot']['shotn']):
            return {
                'ok': False,
                'description': 'server has another shotn loaded'
            }
        if self.fine_processor.get_data()['config_name'] != req['shot']['config_name']:
            return {
                'ok': False,
                'description': 'server has shot loaded with another config'
            }
        if self.fine_processor.get_data()['spectral_name'] != req['shot']['spectral_name']:
            return {
                'ok': False,
                'description': 'server has shot loaded with another spectral calibration'
            }
        if self.fine_processor.get_data()['absolute_name'] != req['shot']['absolute_name']:
            return {
                'ok': False,
                'description': 'server has shot loaded with another absolute calibration'
            }

        stored_calc = ccm_energy.StoredCalculator(self.fine_processor.shotn, self.fine_processor.get_data())
        if stored_calc.error is not None:
            return {
                'ok': False,
                'description': 'Stored_calc error "%s"' % stored_calc.error
             }
        result = stored_calc.calc_dynamics(float(req['start']), float(req['stop']), float(req['r']))
        if stored_calc.error is None:
            return result
        return {
            'ok': False,
            'description': 'Stored_calc error "%s"' % stored_calc.error,
            'result': result
        }

    def sht_names(self, req):
        resp = {}
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        shotn = int(req['shotn'])
        if self.sht is None or self.sht.shotn != shotn:
            self.sht = sht.sht(shotn)
        resp['names'] = self.sht.get_names()
        resp['ok'] = True
        return resp

    def sht_signal(self, req):
        resp = {}
        if 'shotn' not in req:
            resp['ok'] = False
            resp['description'] = '"shotn" field is missing from request.'
            return resp
        shotn = int(req['shotn'])
        if self.sht is None or self.sht.shotn != shotn:
            return {
                'ok': False,
                'description': 'server has another sht shotn loaded'
            }
        if 'name' not in req:
            resp['ok'] = False
            resp['description'] = '"name" field is missing from request.'
            return resp
        resp['signal'] = self.sht.get_sig(req['name'])
        resp['ok'] = True
        return resp

    def slow_status(self, req):
        self.slow = SlowADC('%s/%s/%s/' % (DB_PATH, PLASMA_SHOTS, SLOW_RAW_FOLDER))
        if not self.slow.ready or not self.slow.satus():
            print('slow connection error')
            self.state['slow'] = {
                'ok': False,
                'description': ('Connection error')
            }
        else:
            self.state['slow'] = {
                'ok': True
            }
        return self.state['slow']

    def slow_arm(self, req):
        shot_filename = SHOTN_FILE
        if not os.path.isfile(shot_filename):
            self.state['slow'] = {
                'ok': False,
                'description': 'Shotn file "%s" not found.' % shot_filename
            }
            return self.state['slow']
        else:
            with open(shot_filename, 'r') as shotn_file:
                line = shotn_file.readline()
                shotn = int(line)

        self.slow.arm(shotn=shotn)

        self.state['slow'] = {
            'ok': True,
            'armed': True,
            'shotn': shotn
        }
        return self.state['slow']

    def slow_disarm(self, req):
        self.slow.disarm()
        self.state['slow'] = {
            'ok': True,
            'armed': False
        }
        return self.state['slow']

    def fast_status(self, req):
        #print('status...')
        #print(req)
        if 'shotn' in req:
            shotn = req['shotn']
        else:
            #print('wtf')
            if not os.path.isfile(SHOTN_FILE):
                shotn = 0
                self.state['fast'] = {
                    'ok': False,
                    'description': 'Shotn file not found.'
                }
            else:
                shotn = 0
                with open(SHOTN_FILE, 'r') as shotn_file:
                    line = shotn_file.readline()
                    shotn = int(line)
        try:
            caen.connect()
        except ConnectionError as err:
            print('caen connection error', err)
            self.state['fast'] = {
                'ok': False,
                'description': ('Connection error: "%s"' % err)
            }
        else:
            caen.send_cmd(caen.Commands.Alive)
            time.sleep(1)
            resp = caen.read()
            print(resp)
            caen.disconnect()

            if resp['status']:
                self.state['fast'] = {
                    'ok': True,
                    'resp': resp,
                    'shotn': shotn
                }
                #self.crate.connect()
            else:
                self.state['fast'] = resp
        return self.state['fast']

    def fast_arm(self, req):
        if 'isPlasma' not in req:
            return {
                'ok': False,
                'description': '"isPlasma" field is missing from request.'
            }
        isPlasma = req['isPlasma']
        if 'header' not in req:
            return {
                'ok': False,
                'description': '"header" field is missing from request.'
            }
        if 'shotn' in req:
            shotn = int(req['shotn'])
        else:
            shot_filename = "%s%sSHOTN.TXT" % (DB_PATH, DEBUG_SHOTS)
            if isPlasma:
                shot_filename = SHOTN_FILE
            if not os.path.isfile(shot_filename):
                self.state['fast'] = {
                    'ok': False,
                    'description': 'Shotn file "%s" not found.' % shot_filename
                }
                return self.state['fast']
            else:
                with open(shot_filename, 'r') as shotn_file:
                    line = shotn_file.readline()
                    shotn = int(line)
        try:
            caen.connect()
        except ConnectionError as err:
            print('caen connection error', err)
            self.state['fast'] = {
                'ok': False,
                'description': ('Connection error: "%s"' % err)
            }
        else:
            injection = req['header']
            injection.update({

            })
            caen.send_cmd(caen.Commands.Arm, [shotn, isPlasma, injection])
            print(caen.read())

            caen.disconnect()

            if not isPlasma and 'shotn' not in req:
                with open(shot_filename, 'w') as shotn_file:
                    # shotn_file.seek(0)
                    shotn_file.write('%d' % (shotn + 1))

            self.state['fast'] = {
                'ok': True,
                'armed': True,
                'shotn': shotn
            }
        return self.state['fast']

    def fast_disarm(self, req):
        try:
            caen.connect()
        except ConnectionError as err:
            print('caen connection error', err)
            self.state['fast'] = {
                'ok': False,
                'description': ('Connection error: "%s"' % err)
            }
        else:
            caen.send_cmd(caen.Commands.Disarm)
            caen.read()

            time.sleep(0.5)
            caen.disconnect()
            self.state['fast'] = {
                'ok': True,
                'armed': False
            }
        return self.state['fast']

    def las_connect(self, req):
        self.state['las'] = self.las.connect()
        self.state['las_cool'] = self.las_cool.connect()
        self.tokamak.connect()
        return self.state['las']

    def las_status(self, req):
        self.state['las'] = self.las.status()
        return self.state['las']

    def las_fire(self, req):
        self.state['las'] = self.las.set_state_3()
        return self.state['las']

    def las_idle(self, req):
        self.state['las'] = self.las.set_state_1()
        return self.state['las']

    def diag_status(self, req):
        self.las_status({})
        self.state['las']['delays'] = self.las.get_energy()
        self.fast_status({})
        self.state['coolant'] = self.las_cool.log
        self.state['tokamak'] = self.tokamak.log
        #self.state['crate'] = self.crate.log
        return self.state

    def diag_disarm(self):
        self.fast_disarm({})
        self.las_idle({})
        print('auto disarmed')

    def arm_all(self, req):
        shot_filename = SHOTN_FILE
        if not os.path.isfile(shot_filename):
            return {
                'ok': False,
                'description': 'Shotn file "%s" not found.' % shot_filename
            }
        if 'header' not in req:
            return {
                'ok': False,
                'description': '"header" field is missing from request.'
            }
        with open(shot_filename, 'r') as shotn_file:
            line = shotn_file.readline()
            shotn = int(line)
        try:
            caen.connect()
            caen.send_cmd(caen.Commands.Arm, [shotn, True, req['header']])
            print(caen.read())

            caen.disconnect()

            las = self.las_fire(req)

            # set flag here

            return {
                'ok': True,
                'shotn': shotn,
                'las': las
            }
        except ConnectionError as err:
            print('caen connection error', err)
            return {
                'ok': False,
                'description': ('Connection error: "%s"' % err)
            }

    def get_db_shot(self, req):
        if 'shotn' not in req:
            return {
                'ok': False,
                'description': '"shotn" field is missing from request.'
            }
        if not isinstance(req['shotn'], int):
            return {
                'ok': False,
                'description': '"%s" is not a valid integer shotnumber.' % req['shotn']
            }
        data = self.db.get_shot(req['shotn'])
        if 'ok' not in data:
            return {
                'ok': False,
                'description': 'Internal db error.',
                'aux': data
            }
        return data

    def get_db_shot_ver(self, req):

        if 'shotn' not in req:
            return {
                'ok': False,
                'description': '"shotn" field is missing from request.'
            }
        if not isinstance(req['shotn'], int):
            return {
                'ok': False,
                'description': '"%s" is not a valid integer shotnumber.' % req['shotn']
            }

        result_folder = '%s%05d/' % (self.plasma_verified_path, int(req['shotn']))
        if not os.path.isdir(result_folder):
            return {
                'ok': False,
                'description': 'Verified shotn "%s" does not exist' % req['shotn']
            }

        if 'ver' not in req:
            req['ver'] = -1
            with open('%sdefault.txt' % result_folder, 'r') as file:
                req['ver'] = 'v%02d' % int(file.readline())
            if req['ver'] == -1:
                return {
                    'ok': False,
                    'description': 'Corrupted default version'
                }

        resp = {
            'ok': True,
            'shot': self.get_version(req)['res']
        }
        if not resp['shot']['ok']:
            return resp
        resp['cfm'] = self.load_ccm(resp)
        return resp

    def get_configs(self, req):
        resp = {}

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

    def calc_cfm(self, req):
        if 'shotn' not in req:
            return {
                'ok': False,
                'description': '"shotn" field is missing from request.'
            }

        filename = '%smcc_%s.json' % (CFM_DB, req['shotn'])
        if not os.path.isfile(filename):
            filename = '%smcc_%s.json' % (CFM_DB_NEW, req['shotn'])
            if not os.path.isfile(filename):
                serv_resp = requests.post(CFM_ADDR, json={
                    'changedPropIds': ["btn-2.n_clicks"],
                    'inputs': [
                        {
                            'id': "btn-2",
                            'property': "n_clicks",
                            'value': 1
                        }
                    ],
                    'output': "my-output1.children",
                    'outputs': {
                        'id': "my-output1",
                        'property': "children"
                    },
                    'state': [
                        {
                            'id': "shot_number_input",
                            'property': "value",
                            'value': req['shotn']}
                    ]
                })

                if serv_resp.json()['response']['my-output1']['children'].startswith(' Good! '):
                    return {
                        'ok': True
                    }
                return {
                    'ok': False,
                    'description': serv_resp.json()['response']['children']
                }
        return {
            'ok': True
        }

    def dump_dynamics(self, shot, data, x_from: float, x_to:float):
        to_pack = {}
        aux = ''
        if data is not None:
            timestamps = []
            nl42 = []
            nl42_err = []
            # расстояние до сепаратрисы
            # температура и концентрация на сепаратрисе
            # градиент на сепаратрисе
            nl_ave = []
            nl_ave_err = []
            n_ave = []
            n_ave_err = []
            t_ave = []
            t_ave_err = []
            we = []
            we_err = []
            dwe = []
            vol = []
            t_c = []
            t_c_err = []
            n_c = []
            n_c_err = []
            t_p = []
            n_p = []
            r_sep_arr = []
            cfm_timestamps = []
            nl_eq = []
            nl_eq_err = []
            eq_length = []
            nl_eq_ave = []
            nl_eq_ave_err = []

            aux += 'index, time, nl42, nl42_err, l42, <n>42, <n>42_err, <n>V, <n>V_err, <T>V, <T>V_err, We, We_err, dWe/dt, vol, T_center, T_c_err, n_center, n_c_err, T_peaking, n_peaking, R_sep, nl_eq, nl_eq_err, len_eq, <n>eq, <n>eq_err\n'
            aux += '1, ms, m-2, m-2, m, m-3, m-3, m-3, m-3, eV, eV, J, J, kW, m3, eV, eV, m-3, m-3, 1, 1, cm, m-2, m-2, m, m-3, m-3\n'
            for event_ind_aux in range(len(data)):
                event = data[event_ind_aux]

                event_ind = event['event_index']
                if 'error' in event:
                    continue
                if x_from <= shot['events'][event_ind]['timestamp'] <= x_to:
                    if 'error' not in event['data'] and len(event['data']['nl_profile']) != 0:
                        length = (event['data']['nl_profile'][0]['z'] - event['data']['nl_profile'][-1]['z']) * 1e-2
                        length_eq = math.sqrt(math.pow((event['data']['surfaces'][0]['r_max']), 2) - (17 * 17)) * 2 * 1e-2
                        eq_length.append(length_eq)
                        we_derivative = 0
                        if len(data) > 1:
                            if 'error' in data[event_ind_aux]:
                                we_derivative = 0
                            elif event_ind_aux == 0:
                                if 'error' not in data[event_ind_aux + 1]:
                                    we_derivative = (data[event_ind_aux + 1]['data']['vol_w'] - event['data'][
                                        'vol_w']) / (shot['events'][
                                                                      data[event_ind_aux + 1]['event_index']]['timestamp'] -
                                                                  shot['events'][event_ind]['timestamp'])
                            elif event_ind_aux == len(data) - 1:
                                if 'error' not in data[event_ind_aux - 1]:
                                    we_derivative = (data[event_ind_aux - 1]['data']['vol_w'] - event['data'][
                                        'vol_w']) / (shot['events'][
                                                                      data[event_ind_aux - 1]['event_index']]['timestamp'] -
                                                                  shot['events'][event_ind]['timestamp'])

                            elif len(data) > 2 and 'error' not in data[event_ind_aux - 1] and 'error' not in data[event_ind_aux + 1] and 'error' not in data[event_ind_aux - 1]['data'] and 'error' not in data[event_ind_aux + 1]['data']:
                                we_derivative = (data[event_ind_aux + 1]['data']['vol_w'] -
                                                 data[event_ind_aux - 1]['data']['vol_w']) / \
                                                (shot['events'][data[event_ind_aux + 1]['event_index']][
                                                     'timestamp'] -
                                                 shot['events'][data[event_ind_aux - 1]['event_index']][
                                                     'timestamp'])

                        timestamps.append(shot['events'][event_ind]['timestamp'] * 1e-3)
                        nl42.append(event['data']['nl'])
                        nl42_err.append(event['data']['nl_err'])

                        nl_ave.append(event['data']['nl'] / length)
                        nl_ave_err.append(event['data']['nl_err'] / length)

                        n_ave.append(event['data']['n_vol'])
                        n_ave_err.append(event['data']['n_vol_err'])

                        t_ave.append(event['data']['t_vol'])
                        t_ave_err.append(event['data']['t_vol_err'])

                        we.append(event['data']['vol_w'])
                        we_err.append(event['data']['w_err'])

                        dwe.append(we_derivative)
                        vol.append(event['data']['vol'])

                        t_c.append(event['data']['surfaces'][-1]['Te'])
                        t_c_err.append(event['data']['surfaces'][-1]['Te_err'])

                        n_c.append(event['data']['surfaces'][-1]['ne'])
                        n_c_err.append(event['data']['surfaces'][-1]['ne_err'])

                        t_p.append(event['data']['surfaces'][-1]['Te'] / event['data']['t_vol'])
                        n_p.append(event['data']['surfaces'][-1]['ne'] / event['data']['n_vol'])

                        nl_eq.append(event['data']['nl_eq'])
                        nl_eq_err.append(event['data']['nl_eq_err'])

                        nl_eq_ave.append(event['data']['nl_eq'] / length_eq)
                        nl_eq_ave_err.append(event['data']['nl_eq_err'] / length_eq)

                        surf = event['data']['surfaces'][0]
                        r_sep_val = -1
                        for surf_ind in range(len(surf['z']) - 1):
                            if surf['z'][surf_ind] >= 0 > surf['z'][surf_ind + 1] and surf['r'][surf_ind] > 40:
                                r_sep_val = surf['r'][surf_ind]
                                r_sep_arr.append(r_sep_val)
                                cfm_timestamps.append(timestamps[-1])
                                break
                            else:
                                r_sep_val = -1


                        aux += '%d, %.1f, %.2e, %.2e, %.2f, %.2e, %.2e, %.2e, %.2e, %.2f, %.2f, %d, %d, %d, %.3f, %.2f, %.2f, %.2e, %.2e, %.3f, %.3f, %.2f, %.2e, %.2e, %.2f, %.2e, %.2e\n' % \
                               (event_ind, shot['events'][event_ind]['timestamp'],
                                event['data']['nl'], event['data']['nl_err'],
                                length,
                                event['data']['nl'] / length, event['data']['nl_err'] / length,
                                event['data']['n_vol'], event['data']['n_vol_err'],
                                event['data']['t_vol'], event['data']['t_vol_err'],
                                event['data']['vol_w'], event['data']['w_err'], we_derivative,
                                event['data']['vol'],
                                event['data']['surfaces'][-1]['Te'], event['data']['surfaces'][-1]['Te_err'],
                                event['data']['surfaces'][-1]['ne'],
                                event['data']['surfaces'][-1]['ne_err'],
                                event['data']['surfaces'][-1]['Te'] / event['data']['t_vol'],
                                event['data']['surfaces'][-1]['ne'] / event['data']['n_vol'],
                                r_sep_val,
                                event['data']['nl_eq'], event['data']['nl_eq_err'],
                                length_eq,
                                event['data']['nl_eq'] / length_eq, event['data']['nl_eq_err'] / length_eq
                        )
                    else:
                        aux += '%d, %.1f, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --, --\n' % \
                               (event_ind, shot['events'][event_ind]['timestamp'])
            to_pack = {
                'nl42 (m^-2)': {
                    'comment': 'линейная концентрация по хорде R=42',
                    'unit': 'nl42(m^-2)',
                    'x': timestamps,
                    'y': nl42,
                    'err': nl42_err
                },
                'nl_eq (m^-2)': {
                    'comment': 'линейная концентрация по экваториальной хорде',
                    'unit': 'nl_eq(m^-2)',
                    'x': timestamps,
                    'y': nl_eq,
                    'err': nl_eq_err
                },
                '<nl42> (m^-3)': {
                    'comment': 'средняя концентрация по хорде R=42',
                    'unit': '<nl42>(m^-3)',
                    'x': timestamps,
                    'y': nl_ave,
                    'err': nl_ave_err
                },
                '<nl_eq> (m^-3)': {
                    'comment': 'средняя концентрация по экваториальной хорде',
                    'unit': '<nl_eq>(m^-3)',
                    'x': timestamps,
                    'y': nl_eq_ave,
                    'err': nl_eq_ave_err
                },
                '<ne> (m^-3)': {
                    'comment': 'средняя по объёму концентрация',
                    'unit': '<n>(m^-3)',
                    'x': timestamps,
                    'y': n_ave,
                    'err': n_ave_err
                },
                '<Te>': {
                    'comment': 'средняя по объёму температура',
                    'unit': '<Te>(eV)',
                    'x': timestamps,
                    'y': t_ave,
                    'err': t_ave_err
                },
                'We': {
                    'comment': 'энергозапас в электронном компоненте',
                    'unit': 'We(J)',
                    'x': timestamps,
                    'y': we,
                    'err': we_err
                },
                'dWe/dt': {
                    'comment': 'производная энергозапаса в электронном компоненте',
                    'unit': 'dWe/dt(kW)',
                    'x': timestamps,
                    'y': dwe
                },
                'plasma volume': {
                    'comment': 'объём плазмы внутри сепаратрисы',
                    'unit': 'V(m^-3)',
                    'x': timestamps,
                    'y': vol
                },
                'Te central': {
                    'comment': 'температура в ближайшей к центру точке',
                    'unit': 'Te(eV)',
                    'x': timestamps,
                    'y': t_c,
                    'err': t_c_err
                },
                'ne central (m^-3)': {
                    'comment': 'концентрация в ближайшей к центру точке',
                    'unit': 'ne(m^-3)',
                    'x': timestamps,
                    'y': n_c,
                    'err': n_c_err
                },
                'Te peaking': {
                    'comment': 'мера пикированности профиля температуры = (Te central) / <Te>',
                    'unit': 'пикированность(1)',
                    'x': timestamps,
                    'y': t_p
                },
                'ne peaking': {
                    'comment': 'мера пикированности профиля концентрации = (ne central) / <ne>',
                    'unit': 'пикированность(1)',
                    'x': timestamps,
                    'y': n_p
                },
                'R_sep положение сепаратрисы': {
                    'comment': 'Большой радиус сепаратрисы в экваториальной плоскости вакуумной камеры на стороне слабого поля',
                    'unit': 'R_sep (cm)',
                    'x': cfm_timestamps,
                    'y': r_sep_arr
                },
                'len_eq (m)': {
                    'comment': 'длина экваториальной хорды',
                    'unit': 'l_eq(m)',
                    'x': timestamps,
                    'y': eq_length
                },
            }

        serialised = [{
            'x': [],
            't': [],
            'te': [],
            'n': [],
            'ne': []
        } for poly in shot['config']['poly']]

        for event_ind in range(len(shot['events'])):
            if 'timestamp' in shot['events'][event_ind]:
                if x_from <= shot['events'][event_ind]['timestamp'] <= x_to:
                    for poly_ind in range(len(shot['events'][event_ind]['T_e'])):
                        poly = shot['events'][event_ind]['T_e'][poly_ind]
                        if poly['error'] is None and not ('hidden' in poly and poly['hidden']):
                            serialised[poly_ind]['x'].append(shot['events'][event_ind]['timestamp'] * 1e-3)
                            serialised[poly_ind]['t'].append(poly['T'])
                            serialised[poly_ind]['te'].append(poly['Terr'])
                            serialised[poly_ind]['n'].append(poly['n'])
                            serialised[poly_ind]['ne'].append(poly['n_err'])
        for poly_ind in range(len(serialised)):
            to_pack['Te R%d' % (shot['config']['poly'][poly_ind]['R'] / 10)] = {
                    'comment': 'локальная температура электронов',
                    'unit': 'Te(eV)',
                    'x': serialised[poly_ind]['x'],
                    'y': serialised[poly_ind]['t'],
                    'err': serialised[poly_ind]['te']
                }
            to_pack['ne R%d' % (shot['config']['poly'][poly_ind]['R'] / 10)] = {
                'comment': 'm^-3, локальная концентрация электронов',
                'unit': 'ne(m^-3)',
                'x': serialised[poly_ind]['x'],
                'y': serialised[poly_ind]['n'],
                'err': serialised[poly_ind]['ne']
            }
        packed = shtRipper.ripper.write(path='%s%s%s/' % (self.plasma_path, RES_FOLDER, shot['shotn']),
                                        filename='TS_%s.sht' % shot['shotn'], data=to_pack)
        if len(packed) != 0:
            print('sht packing error: "%s"' % packed)

        if len(aux) == 0:
            return None
        return aux[:-1]

    def to_csv(self, shot, x_from, x_to, aux_data=None):
        temp_evo = ''
        line = 't, '
        for poly in shot['config']['poly']:
            line += '%.1f, %.1f_err, ' % (poly['R'], poly['R'])
        temp_evo += line[:-2] + '\n'
        line = 'ms, '
        for poly in shot['config']['poly']:
            line += 'eV, eV, '
        temp_evo += line[:-2] + '\n'
        for event_ind in range(len(shot['events'])):
            if 'timestamp' in shot['events'][event_ind]:
                if x_from <= shot['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.1f, ' % shot['events'][event_ind]['timestamp']
                    for poly in shot['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                    temp_evo += line[:-2] + '\n'
        temp_prof = ''
        names = 'R, '
        units = 'mm, '
        for event in shot['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.1f, %.1f_err, ' % (event['timestamp'], event['timestamp'])
                    units += 'eV, eV, '
        temp_prof += names[:-2] + '\n'
        temp_prof += units[:-2] + '\n'
        for poly_ind in range(len(shot['config']['poly'])):
            line = '%.1f, ' % shot['config']['poly'][poly_ind]['R']
            for event in shot['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.1f, %.1f, ' % (event['T_e'][poly_ind]['T'], event['T_e'][poly_ind]['Terr'])
            temp_prof += line[:-2] + '\n'

        dens_evo = ''
        line = 't, '
        for poly in shot['config']['poly']:
            line += '%.1f, %.1f_err, ' % (poly['R'], poly['R'])
        dens_evo += line[:-2] + '\n'
        line = 'ms, '
        for poly in shot['config']['poly']:
            line += 'm-3, m-3, '
        dens_evo += line[:-2] + '\n'
        for event_ind in range(len(shot['events'])):
            if 'timestamp' in shot['events'][event_ind]:
                if x_from <= shot['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.1f, ' % shot['events'][event_ind]['timestamp']
                    for poly in shot['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.2e, %.2e, ' % (poly['n'] , poly['n_err'])
                    dens_evo += line[:-2] + '\n'

        dens_prof = ''
        names = 'R, '
        units = 'mm, '
        for event in shot['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.1f, %.1f_err, ' % (event['timestamp'], event['timestamp'])
                    units += 'm-3, m-3, '
        dens_prof += names[:-2] + '\n'
        dens_prof += units[:-2] + '\n'
        for poly_ind in range(len(shot['config']['poly'])):
            line = '%.1f, ' % shot['config']['poly'][poly_ind]['R']
            for event in shot['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '--, --, '
                        else:
                            line += '%.2e, %.2e, ' % (event['T_e'][poly_ind]['n'],
                                                      event['T_e'][poly_ind]['n_err'])
            dens_prof += line[:-2] + '\n'

        dynamics = self.dump_dynamics(shot, aux_data, x_from, x_to)
        return {
            'ok': True,
            'Tt': temp_evo,
            'TR': temp_prof,
            'nt': dens_evo,
            'nR': dens_prof,
            'aux': dynamics
        }

    def to_old_csv(self, shot, x_from, x_to):
        temp_evo = ''
        line = 't, '
        for poly in shot['config']['poly']:
            line += '%.4fcm, %.4fcm, ' % (poly['R'] * 1e-3, poly['R'] * 1e-3)
        temp_evo += line[:-2] + '\n'
        for event_ind in range(len(shot['events'])):
            if 'timestamp' in shot['events'][event_ind]:
                if x_from <= shot['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.4f, ' % (shot['events'][event_ind]['timestamp'] * 1e-3)
                    for poly in shot['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                    temp_evo += line[:-2] + '\n'
        temp_prof = ''
        names = 'R, '
        for event in shot['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.4fs, %.4fs, ' % (event['timestamp'] * 1e-3, event['timestamp'] * 1e-3)
        temp_prof += names[:-2] + '\n'
        for poly_ind in range(len(shot['config']['poly'])):
            line = '%.4f, ' % (shot['config']['poly'][poly_ind]['R'] * 1e-3)
            for event in shot['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.1f, %.1f, ' % (event['T_e'][poly_ind]['T'], event['T_e'][poly_ind]['Terr'])
            temp_prof += line[:-2] + '\n'

        dens_evo = ''
        line = 't, '
        for poly in shot['config']['poly']:
            line += '%.4fcm, %.4fcm, ' % (poly['R'] * 1e-3, poly['R'] * 1e-3)
        dens_evo += line[:-2] + '\n'
        for event_ind in range(len(shot['events'])):
            if 'timestamp' in shot['events'][event_ind]:
                if x_from <= shot['events'][event_ind]['timestamp'] <= x_to:
                    line = '%.4f, ' % (shot['events'][event_ind]['timestamp'] * 1e-3)
                    for poly in shot['events'][event_ind]['T_e']:
                        if poly['error'] is not None or ('hidden' in poly and poly['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.2e, %.2e, ' % (poly['n'] * 1e-6, poly['n_err'] * 1e-6)
                    dens_evo += line[:-2] + '\n'

        dens_prof = ''
        names = 'R, '
        for event in shot['events']:
            if 'timestamp' in event:
                if x_from <= event['timestamp'] <= x_to:
                    names += '%.4fs, %.4fs, ' % (event['timestamp'] * 1e-3, event['timestamp'] * 1e-3)
        dens_prof += names[:-2] + '\n'
        for poly_ind in range(len(shot['config']['poly'])):
            line = '%.4f, ' % (shot['config']['poly'][poly_ind]['R'] * 1e-3)
            for event in shot['events']:
                if 'timestamp' in event:
                    if x_from <= event['timestamp'] <= x_to:
                        if event['T_e'][poly_ind]['error'] is not None or \
                                ('hidden' in event['T_e'][poly_ind] and event['T_e'][poly_ind]['hidden']):
                            line += '1, 1, '
                        else:
                            line += '%.2e, %.2e, ' % (event['T_e'][poly_ind]['n'] * 1e-6,
                                                      event['T_e'][poly_ind]['n_err'] * 1e-6)
            dens_prof += line[:-2] + '\n'

        return {
            'ok': True,
            'Tt': temp_evo,
            'TR': temp_prof,
            'nt': dens_evo,
            'nR': dens_prof
        }
    def publish(self, req, result):
        path = Path('%s%s/' % (PUB_PATH, result['shotn']))
        if not path.is_dir():
            path.mkdir()
        path = Path('%s/v%d/' % (path, result['version']))
        if not path.is_dir():
            path.mkdir()

        with open('%s/result.%s' % (path, FILE_EXT), 'w') as out_file:
            json.dump(result, out_file, indent=1)
        with open('%s/cfm_res.%s' % (path, FILE_EXT), 'w') as out_file:
            json.dump(req['cfm'], out_file, indent=1)
        with open('%s/info.%s' % (path, FILE_EXT), 'w') as out_file:
            json.dump({
                'config_name': result['config_name'],
                'spectral_name': result['spectral_name'],
                'absolute_name': result['absolute_name'],
                'process_timestamp': result['timestamp'],
                'absolute_correction': result['override']['abs_mult']
            }, out_file, indent=1)
        self.raw_processor.save_processed('%s/signal.%s' % (path, FILE_EXT), result['version'])


        req['from'] = result['override']['t_start']
        req['to'] = result['override']['t_stop']
        req['old'] = True
        if 'cfm' not in req or 'data' not in req['cfm']:
            req['cfm'] = {}
        else:
            req['cfm'] = req['cfm']['data']
        csv = self.export_shot(req)

        with open('%s/%s_T(R).csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['TR'])
        with open('%s/%s_T(t).csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['Tt'])
        with open('%s/%s_n(R).csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['nR'])
        with open('%s/%s_n(t).csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['nt'])
        with open('%s/%s_dynamics.csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['aux'])

        with open('%s/%s_T(R)_old.csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['old']['TR'])
        with open('%s/%s_T(t)_old.csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['old']['Tt'])
        with open('%s/%s_n(R)_old.csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['old']['nR'])
        with open('%s/%s_n(t)_old.csv' % (path, result['shotn']), 'w') as out_file:
            out_file.write(csv['old']['nt'])

        shutil.copy2(src='%s%s%s%s/TS_%s.sht' % (DB_PATH, PLASMA_SHOTS, RES_FOLDER, result['shotn'], result['shotn']),
                     dst=path)

        if req['default']:
            for filename in path.iterdir():
                shutil.copy2(src=filename, dst=path.parent)
            with open('%s%s/default.txt' % (PUB_PATH, result['shotn']), 'w') as out_file:
                out_file.write('%d' % result['version'])
        print('Published OK')
