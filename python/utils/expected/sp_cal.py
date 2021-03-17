import json
import filter
import qe

db_path = 'd:/data/db/'
CALIBR_FOLDER = 'calibration/spectral/'
LAMP_FOLDER = 'calibration/lamp/'
CONFIG_FOLDER = 'config/'
lamp_filename = 'Lab_spectrum.txt'


def integrate(x, y):
    res = 0.0
    if len(x) != len(y):
        fuckOff
    for ind in range(len(x) - 1):
        res += (y[ind] + y[ind + 1]) * 0.5 * (x[ind + 1] - x[ind])
    return res


class SpCal:
    def __init__(self, filename, config_filename, wl_start, wl_stop, wl_step):
        with open('%s%s%s.json' % (db_path, CALIBR_FOLDER, filename), 'r') as calibr_file:
            cal_data = json.load(calibr_file)
        self.lamp_wl = []
        self.lamp_val = []
        with open('%s%s%s' % (db_path, LAMP_FOLDER, lamp_filename), 'r') as lamp_file:
            for line in lamp_file:
                line_split = line.split('	')
                self.lamp_wl.append(float(line_split[0]) * 1000)
                self.lamp_val.append(float(line_split[1]))
        with open('%s%s%s.json' % (db_path, CONFIG_FOLDER, config_filename), 'r') as config_file:
            config = json.load(config_file)
        self.fil = filter.Filters()
        self.apd = qe.APD()
        self.kappas = []
        for poly in range(10):
            if cal_data['poly'][poly]['ind'] != poly != config['poly'][poly]['ind']:
                fuckOff
            kappas = []
            for ch in range(5):
                wl = [wl_start]
                integrand = [self.get_spectrum(wl[-1]) * self.apd.qe(wl[-1]) * self.fil.transmission(ch + 1, wl[-1])]
                while wl[-1] <= wl_stop:
                    integrand.append(self.get_spectrum(wl[-1]) * self.apd.qe(wl[-1]) *
                                     self.fil.transmission(ch + 1, wl[-1]))
                    wl.append(wl[-1] + wl_step)
                kappas.append((cal_data['poly'][poly]['u'][ch] - cal_data['poly'][poly]['dark'][ch]) /
                              (integrate(wl, integrand) * config['poly'][poly]['channels'][ch]['slow_gain']))
            self.kappas.append(kappas)

    def get_spectrum(self, wl):
        if wl <= self.lamp_wl[0] or wl >= self.lamp_wl[-1]:
            return 0.0
        for ind in range(len(self.lamp_wl) - 1):
            if self.lamp_wl[ind] <= wl < self.lamp_wl[ind + 1]:
                return self.lamp_val[ind] + (self.lamp_val[ind + 1] - self.lamp_val[ind]) * (wl - self.lamp_wl[ind]) / \
                       (self.lamp_wl[ind + 1] - self.lamp_wl[ind])
        print(self.lamp_wl[0], wl, self.lamp_wl[-1])
        return fuckOff

    def kappa(self, poly, ch):
        return self.kappas[poly][ch - 1] / self.kappas[poly][0]

    def rel_sens(self, poly, ch, wl):
        return self.apd.qe(wl) * self.kappa(poly, ch) * self.fil.transmission(ch, wl)
