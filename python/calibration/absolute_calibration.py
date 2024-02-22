import sys
import os
import auxiliary as aux
from pathlib import Path
import msgpack

PACKAGE_PARENT = '..'  # "python" directory
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from process import rawToSignals


class Spectrum:
    B0_vibr = 1.98973e2  # [1/m] rotational constant for the lowest vibrational level B0
    #Q_norm = 462.41585  # [1] rotational partition function (normalisation constant)
    Q_norm = 1.0  # [1] rotational partition function (normalisation constant) will be calculated
    I_nucl = 1  # [1] nuclear spin
    gamma_sq = 0.51e-60  # [m^6] square of polarizability tensor anisotropy
    J_max = 80

    csv_header = 2

    def get_fraction(self, j:int):  # [1] return fraction of molecules in the state J
        g: int = 6  # statistical weight factor
        if j % 2:
            g = 3

        energy = j * (j + 1) * aux.phys_const.h * aux.phys_const.c * self.B0_vibr  # [J] return rotational energy Ej

        return (1 / self.Q_norm) * g * (2 * j + 1) * aux.math.exp(
            -energy / (aux.phys_const.k_b * self.temperature))  # can be optimized

    def get_raman_shift(self, j: int):  # [1/m] return wavenumber shift
        if j > 0:
            return (4 * j - 2) * self.B0_vibr  # antistocs
        else:
            return -(4 * -j + 6) * self.B0_vibr  # stocs

    def get_raman_wavelength(self, j):  # [m] return shifted wavelength for given laser and j
        return 1 / (
            (1 / self.lambda_las) + self.get_raman_shift(j)
        )

    def get_raman_section(self, j: int, polar: bool = False):  # [m^2 / sr] return differential cross-section
        first = 64 * aux.math.pow(aux.math.pi, 4) / 45
        if j > 0:
            sec = 3 * j * (j - 1) / (2 * (2 * j + 1) * (2 * j - 1))  # antistocs
        else:
            sec = (3 * (-j + 1) * (-j + 2)) / (2 * (2 * -j + 1) * (2 * -j + 3))
        third = aux.math.pow((1 / self.lambda_las) + self.get_raman_shift(j), 4)
        #res = first * sec * third * self.gamma_sq
        print('\n\n\n\n!!!!!!!!!!!!!!!!!!wtf!!!!!!!!!!!!!!!!\n\n\n\n')
        res = first * sec * third * self.gamma_sq * (8 * aux.math.pi * 3)
        if polar:
            #print('Polarizer ON!')
            return res  # depolarized rejected
        return res * (1 + 0.75)  # depolarized accepted = sigmaZZ * 7/4

    def normalise(self):
        q_val = 0
        for j in range(0, self.J_max + 1):
            q_val += self.get_fraction(j)
        self.Q_norm = q_val

    def __init__(self, lambda_las: float, temperature: float, polar: bool = False):
        self.lambda_las: float = lambda_las
        self.temperature = temperature
        self.normalise()
        self.lines = []
        for j in range(2, self.J_max + 1):
            fj = self.get_fraction(j)
            sigma = self.get_raman_section(j, polar=polar)
            #print(self.get_raman_wavelength(j) * 1e9, sigma)
            self.lines.append({
                'J': j,
                'wl': self.get_raman_wavelength(j) * 1e9,
                'line': fj * sigma
            })


calibr_path = 'calibration/abs/'
ophir_path = 'calibration/energy/'
PROCESSED_PATH = 'processed/'
#abs_filename = '2023.01.16_raw_330Hz_1.6J_G2-10'
abs_filename = '2023.10.12_raw'
nl_correction: float = 1.0 #5.8 #1.05e1
#nl_correction: float = 5.7 #5.8 #1.05e1
use_first_shots: int = 100 # or -1


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
        'polarizator': False,
        'laser_energy': abs_calibration['laser_energy'],
        'laser_shots': []
    }
    if 'polar' in abs_calibration:
        result['polarizator'] = abs_calibration['polar']

    poly = []
    laser: float = 0
    las_count = 0
    config = None
    for i,shotn in enumerate(point['shotn']):
        #ophir_file = '%s%s959905_%d.txt' % (aux.DB_PATH, ophir_path, point['ophir'][i])
        ophir = []
        if abs_calibration['version'] < 2:
            ophir_file = '%s%s%s.txt' % (aux.DB_PATH, ophir_path, point['ophir'][i])
            with open(ophir_file, 'r') as file:
                first: bool = True
                count: int = 0
                for line in file:
                    if line[0] == ';' or line[0] == '!' or len(line) <= 1:
                        continue
                    if first:
                        first = False
                        continue
                    if use_first_shots > 0 and count >= use_first_shots:
                        break
                    ophir.append(float(line.split()[1]))
                    count += 1
        else:
                path: Path = Path('%splasma/ophir/%05d.msgpk' % (aux.DB_PATH, shotn))
                if not path.is_file():
                    print('Ophir file is requested but not found')
                    fuck
                with open(path, 'rb') as file:
                    data = msgpack.unpackb(file.read())
                    for event in data:
                        ophir.append(event[1])
        with rawToSignals.Integrator(db_path=aux.DB_PATH, shotn=shotn, is_plasma=False, config_name=abs_calibration['config']) as integrator:
            if len(poly) == 0:
                config = integrator.config
                poly = [[{
                        'signals': [],
                        'weight': 0.0,
                        'val': 0.0
                    } for ch in poly['channels']]
                 for poly in integrator.config['poly']]

            result['shotn'].append(shotn)



            if use_first_shots > 0:
                integrator.processed = integrator.processed[:use_first_shots]
            for ind, event in enumerate(integrator.processed):
                if event['error'] is not None:
                    print('%d event skipped!' % shotn)
                    continue
                result['laser_shots'].append(event['laser']['ave']['int'])
                #laser += event['laser']['ave']['int']

                laser += ophir[ind]
                las_count += 1
                for poly_ind in event['poly']:
                    for ch_ind in range(len(integrator.config['poly'][int(poly_ind)]['channels'])):
                        if event['poly'][poly_ind]['ch'][ch_ind]['error'] is not None:
                            continue
                        poly[int(poly_ind)][ch_ind]['signals'].append(event['poly'][poly_ind]['ch'][ch_ind]['ph_el'] / ophir[ind])

    measured_energy: float = laser / las_count
    result['J_from_ophir'] = abs_calibration['laser_energy'] / measured_energy
    lines = Spectrum(lambda_las=config['laser'][0]['wavelength'] * 1e-9,
                     temperature=aux.phys_const.cels_to_kelv(abs_calibration['temperature']),
                     polar=result['polarizator']).lines
    for poly_ind in range(len(poly)):
        filters = aux.Filters(config['poly'][poly_ind]['filter_set'])
        detector = aux.APD(config['poly'][poly_ind]['detectors'])

        for ch_ind in range(len(poly[poly_ind])):
            poly[poly_ind][ch_ind]['measured'] = sum(poly[poly_ind][ch_ind]['signals']) / len(poly[poly_ind][ch_ind]['signals'])
            poly[poly_ind][ch_ind]['measured_std'] = aux.statistics.stdev(poly[poly_ind][ch_ind]['signals'], xbar=poly[poly_ind][ch_ind]['measured'])
            if stray is not None:
                poly[poly_ind][ch_ind]['measured_w/o_stray'] = poly[poly_ind][ch_ind]['measured'] - \
                                                               stray['poly'][poly_ind][ch_ind]['measured']
                total_sig = 0
                #j = 2
                for line in lines:
                    #total_sig += line['line'] * filters.transmission(ch=ch_ind + 1, wl=line['wl']) * detector.aw(wl=line['wl']) / (line['wl'] * 1e-9)
                    total_sig += line['line'] * filters.transmission(ch=ch_ind + 1, wl=line['wl']) * detector.aw(wl=line['wl']) / (line['wl'])
                    #if poly_ind == 5 and ch_ind == 0:
                    #    print('J = %d, sigma_RS*F = %.1e, T = %.1e, R = %.1e, lambda = %.2f' % (j, line['line'], filters.transmission(ch=ch_ind + 1, wl=line['wl']), detector.aw(wl=line['wl']), line['wl']))
                    #    j += 1

                if aux.math.isnan(total_sig) or total_sig < 1e-49:
                    poly[poly_ind][ch_ind]['A'] = -1
                else:
                    #poly[poly_ind][ch_ind]['A'] = poly[poly_ind][ch_ind]['measured_w/o_stray'] * aux.phys_const.q_e / (nl_correction * stray['spectral']['poly'][poly_ind]['ae'][ch_ind] * abs_calibration['laser_energy'] * config['laser'][0]['wavelength'] * total_sig)
                    #poly[poly_ind][ch_ind]['A'] = poly[poly_ind][ch_ind]['measured_w/o_stray'] * measured_energy / (nl_correction * stray['spectral']['poly'][poly_ind]['ae'][ch_ind] * abs_calibration['laser_energy'] * total_sig * n_N2)

                    poly[poly_ind][ch_ind]['A'] = poly[poly_ind][ch_ind]['measured_w/o_stray'] / (result['J_from_ophir'] * nl_correction * stray['spectral']['poly'][poly_ind]['ae'][ch_ind] * abs_calibration['laser_energy'] * total_sig * n_N2)

                    #if poly_ind == 5 and ch_ind == 0:
                    #    print('A = %.1e, N_RS = %.1e, nl_corr= %.1e, ae= %.1e, Elas= %.1e, sum= %.1e, n_n2= %.1e, ' % (poly[poly_ind][ch_ind]['A'], poly[poly_ind][ch_ind]['measured_w/o_stray'], nl_correction,  stray['spectral']['poly'][poly_ind]['ae'][ch_ind], abs_calibration['laser_energy'], total_sig, n_N2))
                    #    fuck

    result['poly'] = poly
    return result


print('processing stray')
stray = process_point(abs_calibration['stray'], stray=None)
with open('%s%s%s%s%s' % (aux.DB_PATH, aux.CALIBRATION_FOLDER, aux.EXPECTED_FOLDER, abs_calibration['spectral'], aux.JSON), 'r') as file:
    stray['spectral'] = aux.json.load(file)

result = []
for point in abs_calibration['data']:
    print('processing point...')
    result.append(process_point(point, stray=stray))
with open('%s.json' % abs_filename, 'w') as out_file:
    aux.json.dump(result, out_file, indent=2)

calibrated = {
    'abs_raw': abs_filename,
    'A': [],
    'nl_correction': nl_correction,
    'J_from_ophir': result[0]['J_from_ophir'],
    'transmission_to_ophir': 1/result[0]['J_from_ophir']
}
for poly in result[0]['poly']:
    calibrated['A'].append(poly[0]['A'])

with open('%s%s%s%s%s' % (aux.DB_PATH, calibr_path, PROCESSED_PATH, aux.date.today().strftime("%Y.%m.%d"), aux.JSON), 'w') as out_file:
    aux.json.dump(calibrated, out_file, indent=2)

print('__________\n\n')
print('Calibration is completed.')
