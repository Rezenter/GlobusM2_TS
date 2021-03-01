import phys_const as const

db_path = 'd:/data/db/'
APD_FOLDER = 'apd/'


def interpol(x_arr, y_arr, x):
    if len(x_arr) != len(y_arr):
        fuckOff
    if x <= x_arr[0] or x >= x_arr[-1]:
        return 0.0
    for ind in range(len(x_arr) - 1):
        if x_arr[ind] <= x < x_arr[ind + 1]:
            return 0.01 * (y_arr[ind] + (y_arr[ind + 1] - y_arr[ind]) * (x - x_arr[ind]) / (x_arr[ind + 1] - x_arr[ind]))
    print(x_arr[0], x, x_arr[-1])
    return fuckOff


class APD:
    def __init__(self):
        self.apd = {
                'wl': [],
                'qe': []
            }
        '''
        with open('%s%sqe.csv' % (db_path, APD_FOLDER), 'r') as filter_file:
            for line in filter_file:
                splitted = line.split(',')
                self.apd['wl'].append(float(splitted[0]))
                self.apd['qe'].append(float(splitted[1]))
        '''
        with open('%s%saw.csv' % (db_path, APD_FOLDER), 'r') as filter_file:
            for header in range(2):
                filter_file.readline()
            mult = const.h * const.c * 1e9 / const.q_e
            for line in filter_file:
                splitted = line.split(',')
                self.apd['wl'].append(float(splitted[0]))
                self.apd['qe'].append(float(splitted[1]) * mult / self.apd['wl'][-1])

    def qe(self, wl):
        return interpol(self.apd['wl'], self.apd['qe'], wl)
