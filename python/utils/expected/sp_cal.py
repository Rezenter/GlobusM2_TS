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
    def __init__(self, calibr_filename, config_filename, wl_start, wl_stop, wl_step, additional_filter=None):
        self.aux_filter = []
        if additional_filter is not None:
            print('WARNING!!!!\n\n USING ADDITIONAL FILTER!!!\n\n___________________________\n\n')
            with open('aux_filters/%s' % additional_filter, 'r') as file:
                for line in file:
                    split = line.split(', ')
                    self.aux_filter.append({
                        'wl': float(split[0]),
                        't': float(split[1]) * 0.01
                    })

        with open('%s%s%s.json' % (db_path, CALIBR_FOLDER, calibr_filename), 'r') as calibr_file:
            cal_data = json.load(calibr_file)
            self.version: int = 1
            if "version" in cal_data:
                self.version = cal_data['version']
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
                cal_signal = 0
                if self.version == 1:
                    cal_signal = (cal_data['poly'][poly]['u'][ch] - cal_data['poly'][poly]['dark'][ch])
                elif self.version == 2:
                    cal_signal = cal_data['poly'][poly]['amp'][ch]
                kappas.append(cal_signal /
                              (integrate(wl, integrand) * config['poly'][poly]['channels'][ch]['slow_gain']))
            self.kappas.append(kappas)
        #self.dump_rel_sens()  # debug

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
        #return self.apd.qe(wl) * self.fil.transmission(ch, wl) * self.get_aux_filter(wl)  # debug for pictures without spectral calibration
        return self.apd.qe(wl) * self.kappa(poly, ch) * self.fil.transmission(ch, wl) * self.get_aux_filter(wl)

    def get_aux_filter(self, wl):
        if len(self.aux_filter) == 0:
            return 1
        for i in range(len(self.aux_filter) - 1):
            if self.aux_filter[i]['wl'] <= wl < self.aux_filter[i + 1]['wl']:
                return self.aux_filter[i]['t'] + (self.aux_filter[i + 1]['t'] - self.aux_filter[i]['t']) * \
                       (wl - self.aux_filter[i]['wl']) / (self.aux_filter[i + 1]['wl'] - self.aux_filter[i]['wl'])
        print(self.aux_filter[0], wl, self.aux_filter[-1])
        fuck

    def dump_rel_sens(self):
        for poly_ind in range(10):
            print('poly %d' % poly_ind)
            with open('dump/poly_%d.csv' % poly_ind, 'w') as file:
                file.write('wl, ch1, ch2, ch3, ch4, ch5\n')
                file.write('nm, , , , , \n')
                for wl in range(700, 1064):
                    line = '%d, ' % wl
                    for ch_ind in range(5):
                        line += '%.3f, ' % self.rel_sens(poly_ind, ch_ind + 1, wl)
                    file.write(line[:-2] + '\n')
        print('ok')
        fuck