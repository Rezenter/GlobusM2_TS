import statistics
import sys
import os

PACKAGE_PARENT = '../..'  # "python" directory
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from process import rawToSignals

import spectrum

import phys_const
import json
import math

db_path = 'd:/data/db/'
calibr_path = 'calibration/abs/'

abs_filename = '2021.10.18_raw'
ch = 0
nl_correction = 13.3


with open('%s%s%s.json' % (db_path, calibr_path, abs_filename), 'r') as abs_file:
    abs_calibration = json.load(abs_file)

stray = None

def process_point(point):
    n_N2 = phys_const.torr_to_pa(point['pressure']) / (phys_const.k_b * (phys_const.cels_to_kelv(abs_calibration['temperature'])))

    laser = 0

    result = {
        'n_N2': n_N2,
        'shotn': [],
        'pressure': point['pressure'],
        'temperature': abs_calibration['temperature'],
        'laser_energy': abs_calibration['laser_energy'],
        'measured': [],
        'measured_std': [],
        'A': [],
        'measured_w/o_stray': [],
        'E_mult': 1
    }
    if stray is not None:
        result['stray'] = stray['measured']
        result['stray_std'] = stray['measured_std']

    signals = [{'val': 0, 'weight': 0, 'signals': []} for poly in range(10)]

    for shotn in point['shotn']:

        with rawToSignals.Integrator(db_path, shotn, False, abs_calibration['config']) as integrator:
            result['shotn'].append(shotn)

            for event in integrator.processed:
                if event['error'] is not None:
                    print('%d event skipped!' % shotn)
                    continue
                laser += event['laser']['ave']['int']
                for poly_ind in event['poly']:
                    if event['poly'][poly_ind]['ch'][ch]['error'] is not None:
                        continue
                    signals[int(poly_ind)]['signals'].append(event['poly'][poly_ind]['ch'][ch]['ph_el'])
                    signals[int(poly_ind)]['weight'] += math.pow(event['poly'][poly_ind]['ch'][ch]['err'], -2)
                    signals[int(poly_ind)]['val'] += event['poly'][poly_ind]['ch'][ch]['ph_el'] *\
                                                math.pow(event['poly'][poly_ind]['ch'][ch]['err'], -2)

    for poly_ind in range(len(signals)):
        result['measured'].append(signals[poly_ind]['val'] / signals[poly_ind]['weight'])
        result['measured_std'].append(statistics.stdev(signals[poly_ind]['signals'], xbar=result['measured'][poly_ind]))
        if stray is not None:
            result['measured_w/o_stray'].append(result['measured'][poly_ind] -
                                                            stray['measured'][poly_ind])
            result['A'].append(result['measured_w/o_stray'][poly_ind] /
                               (n_N2 * abs_calibration['laser_energy'] * spectrum.get_sum(ch + 1)) /
                               nl_correction)
    result['J_from_int'] = abs_calibration['laser_energy'] * len(signals[0]['signals']) / laser

    with open('%s.json' % abs_filename, 'w') as out_file:
        json.dump(result, out_file)
    return result


stray = process_point(abs_calibration['stray'])
for point in abs_calibration['data']:
    process_point(point)

print('Calibration is completed.')
