import scipy.special as sci
import auxiliary as aux

# change only these lines!
spectral_raw_name: str = '2023.10.06'
WL_STEP: float = 0.05  # [nm]. integration step, 0.1
T_LOW: float = 5.0  # [eV]
T_HIGH: float = 5000  # [eV]
T_MULT: float = 1.01  # default = 1.01

config_name: str = '2023.07.04_DIVERTOR_G10' # not used for version 3+
# change only these lines!

class TS_spectrum:
    def __init__(self, theta_deg: float, model: str = 'Naito', lambda0: float = 1064.5):
        self.theta: float = aux.phys_const.deg_to_rad(theta_deg)
        self.sin_theta: float = aux.math.sin(self.theta)
        self.cos_theta: float = aux.math.cos(self.theta)
        self.lambda_0: float = lambda0  # [nm], laser wavelength
        if model == 'Selden':
            self.model: int = 0
            self.alphaT: float = aux.phys_const.m_e * aux.phys_const.c**2 / (2 * aux.phys_const.q_e)

        elif model == 'Naito':
            self.model: int = 1
            self.t_low = 750  # switch to selden for low temp
            self.u2: float = (aux.math.sin(self.theta) / (1 - aux.math.cos(self.theta)))**2
            self.alphaT: float = aux.phys_const.m_e * aux.phys_const.c ** 2 / (2 * aux.phys_const.q_e)  # for low-temp

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
            a_loc: float = aux.math.pow(1 + x, 3) * aux.math.sqrt(2 * (1 - self.cos_theta) * (1 + x) + aux.math.pow(x, 2))
            b_loc: float = aux.math.sqrt(1 + x * x / (2 * (1 - self.cos_theta) * (1 + x))) - 1
            c_loc: float = aux.math.sqrt(alpha / aux.math.pi) * (1 - (15 / 16) / alpha + 345 / (512 * alpha * alpha))
            return (c_loc / a_loc) * aux.math.exp(-2 * alpha * b_loc) / self.lambda_0
        elif model == 1:  # Naito
            if temp < self.t_low:
                return self.scat_power_dens(temp=temp, wl=wl, model_override=0)

            alpha2: float = aux.phys_const.m_e * aux.phys_const.c**2 * aux.phys_const.Joule_to_eV / temp
            epsilon: float = (wl - self.lambda_0) / self.lambda_0
            x: float = aux.math.sqrt(1 + epsilon**2 / (2 * (1 - self.cos_theta) * (1 + epsilon)))
            u: float = self.sin_theta / (1 - self.cos_theta)
            y: float = aux.math.pow(x**2 + u**2, -0.5)
            zeta: float = x * y
            eta: float = y / alpha2

            sz: float = aux.math.exp(-alpha2 * x) / (2 * sci.kn(2, alpha2) * (1 + epsilon)**3) * \
                        aux.math.pow(2 * (1 - self.cos_theta) * (1 + epsilon) + epsilon**2, - 0.5)
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

    def __init__(self, spectral_name: str):
        with open('%s%s%s%s%s' % (aux.DB_PATH, aux.CALIBRATION_FOLDER, aux.SPECTRAL_FOLDER, spectral_name, aux.JSON), 'r') as file:
            self.calibration = aux.json.load(file)
            if self.calibration['version'] < 2:
                fuck
            else:
                if self.calibration['version'] >= 3:
                    with open('%s%s%s%s' % (aux.DB_PATH, aux.CONFIG_FOLDER, self.calibration['config'], aux.JSON), 'r') as file:
                        self.config = aux.json.load(file)
                else:
                    with open('%s%s%s%s' % (aux.DB_PATH, aux.CONFIG_FOLDER, config_name, aux.JSON), 'r') as file:
                        self.config = aux.json.load(file)

        if self.config['type version'] < 1:
            fuck

        self.lamp = {
            'x': [],  # [nm] wavelength
            'y': []
        }
        with open('%s%s%s' % (aux.DB_PATH, aux.CALIBRATION_FOLDER, aux.LAMP), 'r') as file:
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
            poly_conf['filters'] = aux.Filters(poly_conf['filter_set'])
            poly_conf['detector'] = aux.APD(poly_conf['detectors'])
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
                    integral += aux.phys_const.interpolate_arr(x_arr=self.lamp['x'], y_arr=self.lamp['y'], x_tgt=wl) * \
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

        with open('%s%s%s%s_debug%s' % (aux.DB_PATH, aux.CALIBRATION_FOLDER, aux.EXPECTED_FOLDER, aux.date.today().strftime("%Y.%m.%d"), aux.JSON), 'w') as file:
            result = {
                'type': 'expected signals',
                'type version': 2,
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
                    'expected': [],
                    'ae': []
                })
                for ch_ind in range(len(poly_conf['channels'])):
                    result['poly'][-1]['expected'].append(poly_conf['channels'][ch_ind]['expected'])
                    result['poly'][-1]['ae'].append(poly_conf['channels'][ch_ind]['ae'])
            aux.json.dump(result, file, indent=2)


expected = ExpectedSignals(lamp_calibration=LampCalibration(spectral_name=spectral_raw_name))

print('Code OK')
