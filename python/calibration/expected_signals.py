import json
import math
from pathlib import Path
import phys_const  # at least v1.3
import scipy.special as sci
from datetime import date

DB_PATH: str = 'd:/data/db/'
FIBER_FOLDER: str = 'fibers/calculated/'
FILTER_FOLDER = 'filters/'
APD_FOLDER = 'apd/'
JSON: str = '.json'
CONFIG_FOLDER: str = 'config/'
CALIBRATION_FOLDER: str = 'calibration/'
SPECTRAL_FOLDER: str = 'spectral/'
LAMP: str = 'lamp/Lab_spectrum.txt'
EXPECTED_FOLDER: str = 'expected/'


# change only these lines!
config_name: str = '2022.06.14'
spectral_raw_name: str = '2022.05.12'
WL_STEP: float = 0.05  # [nm]. integration step, 0.1
T_LOW: float = 1.0  # [eV]
T_HIGH: float = 5e3  # [eV]
T_MULT: float = 1.05
# change only these lines!


class Filters:
    def __init__(self, filter_set: str):
        self.trans = []
        self.name: str = filter_set
        for ch_filename in Path('%s%s%s/' % (DB_PATH, FILTER_FOLDER, filter_set)).iterdir():
            filter = {
                't': [],
                'wl': []
            }
            print(ch_filename)
            with open(ch_filename, 'r') as filter_file:
                for line in filter_file:
                    splitted = line.split(',')
                    filter['wl'].append(float(splitted[0]))
                    filter['t'].append(0.01 * float(splitted[1]))
                if filter['wl'][0] > filter['wl'][-1]:
                    filter['wl'].reverse()
                    filter['t'].reverse()
            self.trans.append(filter)

    def dump(self):
        with open('%s.csv' % self.name, 'w') as file:
            wl = 700
            file.write('wl, ch1, ch2, ch3, ch4, ch5\n')
            while wl < 1070:
                line = '%.1f, ' % wl
                for ch in range(5):
                    line += '%.3e, ' % self.transmission(ch + 1, wl)
                file.write(line[:-2] + '\n')
                wl += 0.1
        print('filters written to file')

    def transmission(self, ch: int, wl: float) -> float:  # whole polychromator
        if wl >= self.trans[ch - 1]['wl'][-1] or wl <= self.trans[ch - 1]['wl'][0]:
            return 0.0
        res: float = 1
        curr: int = 1
        while curr != ch:
            if wl >= self.trans[curr - 1]['wl'][-1] or wl <= self.trans[curr - 1]['wl'][0]:
                prev: float = 0.0
            else:
                prev: float = max(0.0, phys_const.interpolate_arr(self.trans[curr - 1]['wl'], self.trans[curr - 1]['t'], wl))
            res *= 1 - prev
            curr += 1
        return max(0.0, res * phys_const.interpolate_arr(self.trans[ch - 1]['wl'], self.trans[ch - 1]['t'], wl))


class APD:
    mult: float = 0.01 * phys_const.h * phys_const.c * 1e9 / phys_const.q_e

    def __init__(self, apd_name: str):
        self.apd = {
                'wl': [],
                'qe': [],
                'aw': []
            }
        with open('%s%s%s/aw.csv' % (DB_PATH, APD_FOLDER, apd_name), 'r') as filter_file:
            for header in range(2):
                filter_file.readline()

            for line in filter_file:
                splitted = line.split(',')
                self.apd['wl'].append(float(splitted[0]))
                self.apd['aw'].append(float(splitted[1]))
                self.apd['qe'].append(float(splitted[1]) * self.mult / self.apd['wl'][-1])

    def qe(self, wl: float) -> float:
        return phys_const.interpolate_arr(self.apd['wl'], self.apd['qe'], wl)

    def aw(self, wl: float) -> float:
        return phys_const.interpolate_arr(self.apd['wl'], self.apd['aw'], wl)


class TS_spectrum:
    def __init__(self, theta_deg: float, model: str = 'Naito', lambda0: float = 1064.5):
        self.theta: float = phys_const.deg_to_rad(theta_deg)
        self.sin_theta: float = math.sin(self.theta)
        self.cos_theta: float = math.cos(self.theta)
        self.lambda_0: float = lambda0  # [nm], laser wavelength
        if model == 'Selden':
            self.model: int = 0
            self.alphaT: float = phys_const.m_e * phys_const.c**2 / (2 * phys_const.q_e)

        elif model == 'Naito':
            self.model: int = 1
            self.t_low = 750  # switch to selden for low temp
            self.u2: float = (math.sin(self.theta) / (1 - math.cos(self.theta)))**2
            self.alphaT: float = phys_const.m_e * phys_const.c ** 2 / (2 * phys_const.q_e)  # for low-temp

        else:
            print('Unsupported TS spectrum model "%s". Only "Selden" or "Naito" is implemented' % model)
            self.model: int = -1
            fuckOff
        self.__check_spectrum()

    def scat_power_dens(self, temp: float, wl: float, model_override: int = -1) -> float:  # Scattering Power
        model = self.model
        if model_override != -1:
            model = model_override
        if model == 0:  # Selden
            alpha: float = self.alphaT / temp
            x: float = (wl / self.lambda_0) - 1
            a_loc: float = math.pow(1 + x, 3) * math.sqrt(2 * (1 - self.cos_theta) * (1 + x) + math.pow(x, 2))
            b_loc: float = math.sqrt(1 + x * x / (2 * (1 - self.cos_theta) * (1 + x))) - 1
            c_loc: float = math.sqrt(alpha / math.pi) * (1 - (15 / 16) / alpha + 345 / (512 * alpha * alpha))
            return (c_loc / a_loc) * math.exp(-2 * alpha * b_loc) / self.lambda_0
        elif model == 1:  # Naito
            if temp < self.t_low:
                return self.scat_power_dens(temp=temp, wl=wl, model_override=0)

            alpha2: float = phys_const.m_e * phys_const.c**2 * phys_const.Joule_to_eV / temp
            epsilon: float = (wl - self.lambda_0) / self.lambda_0
            x: float = math.sqrt(1 + epsilon**2 / (2 * (1 - self.cos_theta) * (1 + epsilon)))
            u: float = self.sin_theta / (1 - self.cos_theta)
            y: float = math.pow(x**2 + u**2, -0.5)
            zeta: float = x * y
            eta: float = y / alpha2

            sz: float = math.exp(-alpha2 * x) / (2 * sci.kn(2, alpha2) * (1 + epsilon)**3) * \
                        math.pow(2 * (1 - self.cos_theta) * (1 + epsilon) + epsilon**2, - 0.5)
            q: float = 1 - 4 * eta * zeta * (2 * zeta - (2 - 3 * zeta**2) * eta) / (2 * zeta - (2 - 15 * zeta**2) * eta)
            return sz * q / self.lambda_0
        else:
            return fuckOff

    def __check_spectrum(self) -> bool:
        te_arr: list[float] = [T_LOW, 60, 100, 500, 1e3, 5e3]
        for te in te_arr:
            print('T_e = %.0e' % te)
            total: float = 0.0
            curr_wl: float = self.lambda_0 - WL_STEP * 0.5
            while curr_wl > 100:
                sp_dens = self.scat_power_dens(temp=te, wl=curr_wl)
                total += sp_dens
                if sp_dens < 1e-10:
                    break
                curr_wl -= WL_STEP
            print('blue spectral dens integral = %.3f, stop wavelength = %.1f' % (total*WL_STEP, curr_wl))
            curr_wl = self.lambda_0 + WL_STEP * 0.5
            while curr_wl < 10000:
                sp_dens = self.scat_power_dens(temp=te, wl=curr_wl)
                total += sp_dens
                if sp_dens < 1e-10:
                    break
                curr_wl += WL_STEP
            total *= WL_STEP
            print('total spectral dens integral error = %.2e, stop wavelength = %.1f' % (abs(1 - total), curr_wl))
            if not 0.9 < total < 1.1:
                print('Too high error in spectrum! T_e = %.0e, total spectral dens integral = %.3f' % (te, total))
                fuck
                return False
            print('_____________')
        return True


class LampCalibration:
    threshold = 5e-7

    def __init__(self, config, spectral_name: str):
        self.config = config

        if config['type version'] < 1:
            fuck
        with open('%s%s%s%s%s' % (DB_PATH, CALIBRATION_FOLDER, SPECTRAL_FOLDER, spectral_name, JSON), 'r') as file:
            self.calibration = json.load(file)
            if self.calibration['type version'] < 2:
                fuck

        self.lamp = {
            'x': [],  # [nm] wavelength
            'y': []
        }
        with open('%s%s%s' % (DB_PATH, CALIBRATION_FOLDER, LAMP), 'r') as file:
            for line in file:
                splt = line.split()
                self.lamp['x'].append(float(splt[0]) * 1e3)
                self.lamp['y'].append(float(splt[1]))

        for poly_ind_conf, poly_conf in enumerate(self.config['poly']):
            for poly_ind_cal_tmp, poly_cal in enumerate(self.calibration['poly']):
                if poly_cal['ind'] == poly_conf['ind'] and poly_cal['fiber'] == poly_conf['fiber']:
                    if len(poly_cal['amp']) != len(poly_conf['channels']):
                        print('Calibration and config files are incompatible. ch count are different for %d' % poly_conf['ind'])
                        fuck
                    poly_conf['calibr_ind'] = poly_ind_cal_tmp
                    break
            else:
                print('Calibration and config files are incompatible. Could not find poly ind "%d" with fiber "%s"' % (poly_conf['ind'], poly_conf['fiber']))
                fuck

        print('Calculating ae...')
        self.__calc_ae()
        print('Done.')

    def __calc_ae(self):
        for poly_ind_conf, poly_conf in enumerate(self.config['poly']):
            poly_conf['filters'] = Filters(poly_conf['filter_set'])
            poly_conf['detector'] = APD(poly_conf['detectors'])
            for ch_ind in range(len(poly_conf['channels'])):
                integral: float = 0
                wl: float = self.config['laser'][0]['wavelength']
                flag: bool = False
                while wl > 300:
                    transmission: float = poly_conf['filters'].transmission(ch=(ch_ind + 1), wl=wl)
                    if transmission < self.threshold or transmission > 10:
                        if flag:
                            break
                        else:
                            wl -= WL_STEP
                            continue
                    else:
                        if transmission > 0.1:
                            flag = True
                    integral += phys_const.interpolate_arr(x_arr=self.lamp['x'], y_arr=self.lamp['y'], x_tgt=wl) * \
                                transmission * poly_conf['detector'].aw(wl=wl) * WL_STEP / wl
                    wl -= WL_STEP

                poly_conf['channels'][ch_ind]['ae_tmp']: float = self.calibration['poly'][poly_conf['calibr_ind']]['amp'][ch_ind] / (poly_conf['channels'][ch_ind]['slow_gain'] * integral)
                print('p %d, ch %d' % (poly_ind_conf + 1, ch_ind + 1))
            for ch in poly_conf['channels']:
                ch['ae'] = ch['ae_tmp'] / poly_conf['channels'][0]['ae_tmp']


class ExpectedSignals:
    threshold = 5e-7

    def __init__(self, lamp_calibration: LampCalibration):
        temp: list[float] = [T_LOW]
        while temp[-1] < T_HIGH:
            temp.append(temp[-1] * T_MULT)

        for poly_ind_conf, poly_conf in enumerate(lamp_calibration.config['poly']):
            print('processing poly %d...' % (poly_ind_conf + 1))
            angle_deg: float = lamp_calibration.config['fibers'][poly_conf['fiber']]['scattering_angle_deg']
            cross = TS_spectrum(theta_deg=angle_deg, model='Naito', lambda0=lamp_calibration.config['laser'][0]['wavelength'])

            for ch in poly_conf['channels']:
                ch['expected'] = []

            for T in temp:
                for ch_ind in range(len(poly_conf['channels'])):
                    integral: float = 0
                    wl: float = lamp_calibration.config['laser'][0]['wavelength']
                    flag: bool = False
                    while wl > 300:
                        transmission: float = poly_conf['filters'].transmission(ch=(ch_ind + 1), wl=wl)
                        if transmission < self.threshold or transmission > 10:
                            if flag:
                                break
                            else:
                                wl -= WL_STEP
                                continue
                        else:
                            if transmission > 0.1:
                                flag = True
                        integral += cross.scat_power_dens(temp=T, wl=wl) * \
                                    transmission * poly_conf['detector'].aw(wl=wl) * WL_STEP / wl
                        wl -= WL_STEP
                    poly_conf['channels'][ch_ind]['expected'].append(integral * poly_conf['channels'][ch_ind]['ae'])

        with open('%s%s%s%s%s' % (DB_PATH, CALIBRATION_FOLDER, EXPECTED_FOLDER, date.today().strftime("%Y.%m.%d"), JSON), 'w') as file:
            result = {
                'type': 'expected signals',
                'type version': 1,
                'calculated_for_config': config_name,
                'spectral_calibration': spectral_raw_name,
                'wl_step': WL_STEP,
                'Te_low': T_LOW,
                'Te_high': T_HIGH,
                'Te_mult': T_MULT,
                'T_arr': temp,
                'poly': []
            }
            for poly_ind_conf, poly_conf in enumerate(lamp_calibration.config['poly']):
                result['poly'].append({
                    'ind': poly_conf['ind'],
                    'expected': []
                })
                for ch_ind in range(len(poly_conf['channels'])):
                    result['poly'][-1]['expected'].append(poly_conf['channels'][ch_ind]['expected'])
            json.dump(result, file, indent=2)


with open('%s%s%s%s' % (DB_PATH, CONFIG_FOLDER, config_name, JSON), 'r') as file:
    config = json.load(file)

expected = ExpectedSignals(lamp_calibration=LampCalibration(config=config, spectral_name=spectral_raw_name))

print('Code OK')
