db_path = 'd:/data/db/'
FILTER_FOLDER = 'filters/'


def interpol(x_arr, y_arr, x):
    if len(x_arr) != len(y_arr):
        fuckOff
    if x >= x_arr[0] or x <= x_arr[-1]:
        return 0.0
    for ind in range(len(x_arr) - 1):
        if x_arr[ind] >= x > x_arr[ind + 1]:
            return 0.01 * (y_arr[ind] + (y_arr[ind + 1] - y_arr[ind]) * (x - x_arr[ind]) / (x_arr[ind + 1] - x_arr[ind]))
    print(x_arr[0], x, x_arr[-1])
    return fuckOff


class Filters:
    def __init__(self):
        self.trans = []
        for ch in range(5):
            filter = {
                't': [],
                'wl': []
            }
            with open('%s%sch%d.csv' % (db_path, FILTER_FOLDER, ch + 1), 'r') as filter_file:
                for line in filter_file:
                    splitted = line.split(',')
                    filter['wl'].append(float(splitted[0]))
                    filter['t'].append(float(splitted[1]))
            self.trans.append(filter)

    def transmission(self, ch, wl):
        res = 1
        curr = 1
        while curr != ch:
            res *= 1 - interpol(self.trans[curr - 1]['wl'], self.trans[curr - 1]['t'], wl)
            curr += 1
        res *= interpol(self.trans[ch - 1]['wl'], self.trans[ch - 1]['t'], wl)
        return res
