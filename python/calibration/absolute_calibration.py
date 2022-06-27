import sys
import os
import auxiliary as aux

PACKAGE_PARENT = '..'  # "python" directory
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from process import rawToSignals


class Spectrum:
    B0_vibr = 1.98973e2  # [1/m] rotational constant for the lowest vibrational level B0
    Q_norm = 462.41585  # [1] rotational partition function (normalisation constant)
    I_nucl = 1  # [1] nuclear spin
    gamma_sq = 0.51e-60  # [m^6] square of polarizability tensor anisotropy
    J_max = 40

    csv_header = 2

    def get_fraction(self, j, temperature):  # [1] return fraction of molecules in the state J
        g: int = 6  # statistical weight factor
        if j % 2:
            g = 3

        energy = j * (j + 1) * aux.phys_const.h * aux.phys_const.c * self.B0_vibr  # [J] return rotational energy Ej

        return (1 / self.Q_norm) * g * (2 * j + 1) * aux.math.exp(
            -energy / (aux.phys_const.k_b * temperature))  # can be optimized

    def get_raman_shift(self, j):  # [1/m] return wavenumber shift
        if j > 0:
            return (4 * j - 2) * self.B0_vibr  # antistocs
        else:
            return -(4 * -j + 6) * self.B0_vibr  # stocs

    def get_raman_wavelength(self, j, lambda_las):  # [m] return shifted wavelength for given laser and j
        return 1 / (
            (1 / lambda_las) + self.get_raman_shift(j)
        )

    def get_raman_section(self, j, lambda_las):  # [m^2 / sr] return differential cross-section
        first = 64 * aux.math.pow(aux.math.pi, 4) / 45
        if j > 0:
            sec = 3 * j * (j - 1) / (2 * (2 * j + 1) * (2 * j - 1))  # antistocs
        else:
            sec = (3 * (-j + 1) * (-j + 2)) / (2 * (2 * -j + 1) * (2 * -j + 3))
        third = aux.math.pow((1 / lambda_las) + self.get_raman_shift(j), 4)
        return first * sec * third * self.gamma_sq

    def __init__(self, lambda_las: float, temperature: float):
        self.lines = []
        for j in range(2, self.J_max + 1):
            fj = self.get_fraction(j, temperature=temperature)
            sigma = self.get_raman_section(j, lambda_las=lambda_las)
            self.lines.append({
                'J': j,
                'wl': self.get_raman_wavelength(j, lambda_las=lambda_las),
                'line': fj * sigma
            })


calibr_path = 'calibration/abs/'
abs_filename = '2022.05.31_raw'
nl_correction = 1.0

with open('%s%s%s%s' % (aux.DB_PATH, calibr_path, abs_filename, aux.JSON), 'r') as file:
    abs_calibration = aux.json.load(file)

with open('%s%s%s%s' % (aux.DB_PATH, aux.CONFIG_FOLDER, abs_calibration['config'], aux.JSON), 'r') as file:
    config = aux.json.load(file)


def process_point(point, stray=None):
    n_N2 = aux.phys_const.torr_to_pa(point['pressure']) / (aux.phys_const.k_b * (aux.phys_const.cels_to_kelv(abs_calibration['temperature'])))

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
        'E_mult': 1.0
    }
    if stray is not None:
        result['stray'] = stray['measured']
        result['stray_std'] = stray['measured_std']

    signals = []
    laser = 0
    for shotn in point['shotn']:
        with rawToSignals.Integrator(db_path=aux.DB_PATH, shotn=shotn, is_plasma=False, config_name=abs_calibration['config']) as integrator:

            signals.append({'val': 0, 'weight': 0, 'signals': []})  # foreach poly

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
                    signals[int(poly_ind)]['weight'] += aux.math.pow(event['poly'][poly_ind]['ch'][ch]['err'], -2)
                    signals[int(poly_ind)]['val'] += event['poly'][poly_ind]['ch'][ch]['ph_el'] *\
                                                aux.math.pow(event['poly'][poly_ind]['ch'][ch]['err'], -2)

    for poly_ind in range(len(signals)):
        result['measured'].append(signals[poly_ind]['val'] / signals[poly_ind]['weight'])
        result['measured_std'].append(aux.statistics.stdev(signals[poly_ind]['signals'], xbar=result['measured'][poly_ind]))
        if stray is not None:
            result['measured_w/o_stray'].append(result['measured'][poly_ind] -
                                                            stray['measured'][poly_ind])
            result['A'].append(result['measured_w/o_stray'][poly_ind] /
                               (n_N2 * abs_calibration['laser_energy'] * Spectrum.get_sum(ch + 1)) /
                               nl_correction)
    result['J_from_int'] = abs_calibration['laser_energy'] * len(signals[0]['signals']) / laser

    with open('%s.json' % abs_filename, 'w') as out_file:
        aux.json.dump(result, out_file)
    return result


stray = process_point(abs_calibration['stray'], stray=None)
for point in abs_calibration['data']:
    process_point(point, stray=stray)

print('Calibration is completed.')
