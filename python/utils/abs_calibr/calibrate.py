import sys
import os

PACKAGE_PARENT = '../..'  # "python" directory
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from process import rawToSignals

import spectrum

import phys_const
import json

db_path = 'd:/data/db/'
calibr_path = 'calibration/abs/'

abs_filename = '2021.01.22_raw'
abs_calibration = {}
with open('%s%s%s.json' % (db_path, calibr_path, abs_filename), 'r') as abs_file:
    abs_calibration = json.load(abs_file)

stray = None

def process_point(point):
    n_N2 = phys_const.torr_to_pa(point['pressure']) / (phys_const.k_b * (abs_calibration['temperature'] + 273))

    with rawToSignals.Integrator(db_path, point['shotn'], False, '2020.12.08_raman') as integrator:
        signals = {'%d' % poly: {'val': 0,
                                 'weight': 0} for poly in range(10)}
        for event in integrator.processed:
            if event['error'] is not None:
                continue
            for poly_ind in event['poly']:
                if event['poly'][poly_ind]['ch'][0]['error'] is not None:
                    continue
                signals[poly_ind]['weight'] += event['poly'][poly_ind]['ch'][0]['err']
                signals[poly_ind]['val'] += event['poly'][poly_ind]['ch'][0]['ph_el'] * \
                                                event['poly'][poly_ind]['ch'][0]['err']
        result = {
            'expected/A': n_N2,
            'shotn': point['shotn'],
            'pressure': point['pressure'],
            'temperature': abs_calibration['temperature'],
            'laser_energy': abs_calibration['laser_energy'],
            'measured': {},
            'A': {},
            'measured_w/o_stray': {}
        }
        for poly_ind in range(10):
            if stray is None:
                result['measured']['%d' % poly_ind] = signals['%d' % poly_ind]['val'] / signals['%d' % poly_ind]['weight']
            else:
                result['measured']['%d' % poly_ind] = signals['%d' % poly_ind]['val'] / signals['%d' % poly_ind][
                    'weight']
                result['measured_w/o_stray']['%d' % poly_ind] = result['measured']['%d' % poly_ind] - \
                                                                stray['measured']['%d' % poly_ind]
                result['A']['%d' % poly_ind] = result['measured_w/o_stray']['%d' % poly_ind] / \
                                               (n_N2 * abs_calibration['laser_energy'] * spectrum.get_sum(1))

        with open('%05d.json' % point['shotn'], 'w') as out_file:
            json.dump(result, out_file)
    return result


stray = process_point(abs_calibration['stray'])
for point in abs_calibration['data']:
    process_point(point)

print('Calibration is completed.')
