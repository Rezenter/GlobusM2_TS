import json
import math
import os.path

CCM_DB = 'y:/!!!CURRENT_COIL_METHOD/old_mcc/'  # y = \\172.16.12.127
CCM_DB_NEW = 'y:/!!!CURRENT_COIL_METHOD/V3_zad7_mcc/'  # y = \\172.16.12.127

theta_count = 180
gamma_shift = 1
#elong_0 = 1.5
elong_0 = 1
#shaf_shift = 3
shaf_shift = 5.5
#triang_mult = 1
triang_mult = 0.5
linear_count = 3


def angle(x1, y1, cx, cy):
    return math.atan2((y1-cy), (x1 - cx))


def interpol(x_prev, x, x_next, y_prev, y_next):
    return y_prev + (y_next - y_prev) * (x - x_prev) / (x_next - x_prev)


def linearization(x, y):
    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_x2 = 0
    if len(x) <= 1:
        return 1, 0
    for i in range(len(x)):
        sum_x += x[i]
        sum_y += y[i]
        sum_xy += x[i] * y[i]
        sum_x2 += math.pow(x[i], 2)
    if len(x) * sum_x2 - math.pow(sum_x, 2) == 0:
        return 1e10, 0
    a = (len(x) * sum_xy - sum_x * sum_y) / (len(x) * sum_x2 - math.pow(sum_x, 2))
    b = (sum_y - a * sum_x) / len(x)
    return a, b


class CCM:
    data = {}
    timestamps = []
    error = None

    def set_error(self, err):
        print('Error! \n %s' % err)
        self.error = err

    def __init__(self, shotn):
        self.error = None
        filename = '%smcc_%d.json' % (CCM_DB, shotn)
        if not os.path.isfile(filename):
            filename = '%smcc_%d.json' % (CCM_DB_NEW, shotn)
            if not os.path.isfile(filename):
                self.set_error('No mcc file found!')
                return
        with open(filename, 'r') as mcc_file:
            self.data = json.load(mcc_file)
        if self.data is None:
            self.set_error('No mcc file loaded!')
            return
        self.timestamps = self.data['time']['variable']
        self.calculated = [{'calculated': False} for t in self.timestamps]

    def clockwise(self, r, z, t_ind):  # called multiple times for one time?
        #print('clockwize', t_ind, self.data['time']['variable'][t_ind])
        params = self.get_surface_parameters(t_ind)

        count = len(r) // 10
        a1 = angle(r[0], z[0], params['R'], params['Z'])
        a0 = angle(r[count], z[count], params['R'], params['Z'])
        if a1 * a0 >= 0 or r[0] > params['R']:
            direction = a1 - a0
        else:
            if a1 < 0:
                direction = 1
            else:
                direction = -1
        #print(t_ind, a1, a0, direction)
        if direction < 0:
            r = [v for v in reversed(r)]
            z = [v for v in reversed(z)]

        for i in range(0, len(r)):
            if r[i] > params['R']:
                if z[i - 1] >= params['Z'] > z[i]:
                    if i == 0:
                        return r, z
                    start_ind = i - 1
                    res_r = r[start_ind:]
                    res_r.extend(r[:start_ind])
                    res_z = z[start_ind:]
                    res_z.extend(z[:start_ind])
                    return res_r, res_z
        print('WTF? FIX THIS SHIT\n\n')
        return [], []

    def get_surface(self, t_ind, ra=1, theta_count=360):
        sep_r, sep_z = self.clockwise(self.data['boundary']['rbdy']['variable'][t_ind],
                                      self.data['boundary']['zbdy']['variable'][t_ind],
                                      t_ind)
        if ra == 1:
            return sep_r, sep_z
        if ra > 1 or ra < 0:
            print(ra)
            fuck

        theta_step = (math.tau / theta_count)

        params = self.get_surface_parameters(t_ind)
        a = ra * (sep_r[0] - params['R'])
        triang = triang_mult * a * params['triag'] / params['a']
        elong = elong_0 + \
                a * (params['elong'] - elong_0) / params['a']
        shift = shaf_shift * math.pow((1 - math.pow(a / params['a'], 2)), gamma_shift)

        r = []
        z = []
        for theta_ind in range(theta_count + 1):
            theta = theta_step * theta_ind
            r.append(params['R'] + shift +
                     a * (math.cos(theta) - triang * math.pow(math.sin(theta), 2)))
            z.append(params['Z'] + a * elong * math.sin(theta))
        return r, z

    def guess_a(self, requested_r, t_ind, max_a, center_r, lfs=True):
        tolerance = 0.1

        min_a = 0
        iteration = 1
        while 1:
            r, z = self.get_surface(t_ind, ra=((max_a + min_a) * 0.5))

            for index in range(len(r) - 1):
                if z[index] * z[index + 1] <= 0:
                    if lfs:
                        if r[index] > center_r:
                            break
                    else:
                        if r[index] < center_r:
                            break
            else:
                min_a = (max_a + min_a) * 0.5
                iteration += 1
                continue

            candidate_r = interpol(z[index + 1], 0, z[index], r[index + 1], r[index])

            if abs(candidate_r - requested_r) <= tolerance or max_a - min_a < 1e-4:
                #print('FOUND:', (max_a + min_a) * 0.5, iteration, candidate_r, requested_r)
                return (max_a + min_a) * 0.5, r, z
            if lfs:
                if candidate_r > requested_r:
                    max_a = (max_a + min_a) * 0.5
                else:
                    min_a = (max_a + min_a) * 0.5
            else:
                if candidate_r > requested_r:
                    min_a = (max_a + min_a) * 0.5
                else:
                    max_a = (max_a + min_a) * 0.5
            iteration += 1

    def find_poly(self, polys, t_ind):
        params = self.get_surface_parameters(t_ind)
        if 'error' in params:
            return {
                'error': params['error']
            }
        sep_r, sep_z = self.clockwise(self.data['boundary']['rbdy']['variable'][t_ind],
                                      self.data['boundary']['zbdy']['variable'][t_ind],
                                      t_ind)
        if len(sep_r) == 0 or len(sep_z) == 0:
            return []
        equator_r = -1
        if sep_z[0] < 0:
            for index in range(len(sep_r) - 1, -1, -1):
                if sep_z[index] > 0:
                    equator_r = sep_r[index]
                    break
        else:
            for index in range(len(sep_r)):
                if sep_z[index] <= 0:
                    equator_r = sep_r[index]
                    break
        if equator_r < 0:
            return []

        center_r = params['R'] + shaf_shift
        lfs_poly = []
        hfs_poly = []
        for poly_ind in range(len(polys)):
            poly = polys[poly_ind]
            if poly['skip']:
                continue
            if poly['R'] >= center_r:
                lfs_poly.append(poly)
            else:
                hfs_poly.insert(0, poly)

        if len(lfs_poly) == 0 and len(hfs_poly) == 0:
            return []
        result = [{
            'a': 1,
            'r': sep_r,
            'z': sep_z
        }]
        last_a = 1
        for poly in lfs_poly:
            if poly['R'] > equator_r:
                continue
            last_a, poly['r'], poly['z'] = self.guess_a(poly['R'], t_ind, last_a, center_r)
            poly['a'] = last_a
            result.append(poly)
        last_a = 1
        for poly in hfs_poly:
            #check poly inside separatrix!
            last_a, poly['r'], poly['z'] = self.guess_a(poly['R'], t_ind, last_a, center_r, lfs=False)
            poly['a'] = last_a
            for res_ind in range(len(result)):
                if result[res_ind]['a'] < last_a:
                    result.insert(res_ind, poly)
                    break
            else:
                result.append(poly)
        result.append({
            'a': 0,
            'r': center_r,
            'r_min': center_r,
            'r_max': center_r,
            'z': params['Z'],
            'z_min': params['Z'],
            'z_max': params['Z']
        })
        r_arr = []
        T_arr = []
        n_arr = []
        Te_err = 0
        ne_err = 0
        for i in range(3):
            if i >= len(result) - 2:
                break
            poly = result[i + 1]

            r_arr.append(poly['a'])
            T_arr.append(poly['Te'])
            n_arr.append(poly['ne'])
            Te_err = max(Te_err, poly['Te_err'])
            ne_err = max(ne_err, poly['ne_err'])
        #print(result)

        a, b = linearization(r_arr, T_arr)
        result[0]['Te'] = max(0, a * result[0]['a'] + b)
        a, b = linearization(r_arr, n_arr)
        result[0]['ne'] = max(0, a * result[0]['a'] + b)
        result[0]['Te_err'] = Te_err * math.sqrt(3)
        result[0]['ne_err'] = ne_err * math.sqrt(3)

        r_arr = []
        T_arr = []
        n_arr = []
        Te_err = 0
        ne_err = 0
        for i in range(3):
            if i >= len(result) - 2:
                break
            poly = result[-(i + 2)]
            r_arr.append(poly['a'])
            T_arr.append(poly['Te'])
            n_arr.append(poly['ne'])
            Te_err = max(Te_err, poly['Te_err'])
            ne_err = max(ne_err, poly['ne_err'])
        a, b = linearization(r_arr, T_arr)
        result[-1]['Te'] = a * result[-1]['a'] + b
        a, b = linearization(r_arr, n_arr)
        result[-1]['ne'] = a * result[-1]['a'] + b
        result[-1]['Te_err'] = Te_err * math.sqrt(3)
        result[-1]['ne_err'] = ne_err * math.sqrt(3)
        return result

    def get_surface_parameters(self, t_ind):
        if not self.calculated[t_ind]['calculated']:
            left = 0
            right = 0
            top = 0
            bot = 0
            if len(self.data['boundary']['rbdy']['variable'][t_ind]) != len(self.data['boundary']['zbdy']['variable'][t_ind]):
                print('Bad CCM data for t_ind = %d.' % t_ind)
                fuck_off
            if len(self.data['boundary']['rbdy']['variable'][t_ind]) == 0:
                self.calculated[t_ind] = {
                    'calculated': True,
                    'error': 'No data.'
                }
            else:
                for i in range(len(self.data['boundary']['rbdy']['variable'][t_ind])):
                    if self.data['boundary']['rbdy']['variable'][t_ind][left] > self.data['boundary']['rbdy']['variable'][t_ind][i]:
                        left = i
                    elif self.data['boundary']['rbdy']['variable'][t_ind][right] < self.data['boundary']['rbdy']['variable'][t_ind][i]:
                        right = i
                    if self.data['boundary']['zbdy']['variable'][t_ind][top] < self.data['boundary']['zbdy']['variable'][t_ind][i]:
                        top = i
                    elif self.data['boundary']['zbdy']['variable'][t_ind][bot] > self.data['boundary']['zbdy']['variable'][t_ind][i]:
                        bot = i

                self.calculated[t_ind] = {
                    'calculated': True,
                    'left': {
                        'index': left,
                        'r': self.data['boundary']['rbdy']['variable'][t_ind][left],
                        'z': self.data['boundary']['zbdy']['variable'][t_ind][left]
                    },
                    'right': {
                        'index': right,
                        'r': self.data['boundary']['rbdy']['variable'][t_ind][right],
                        'z': self.data['boundary']['zbdy']['variable'][t_ind][right]
                    },
                    'top': {
                        'index': top,
                        'r': self.data['boundary']['rbdy']['variable'][t_ind][top],
                        'z': self.data['boundary']['zbdy']['variable'][t_ind][top]
                    },
                    'bot': {
                        'index': bot,
                        'r': self.data['boundary']['rbdy']['variable'][t_ind][bot],
                        'z': self.data['boundary']['zbdy']['variable'][t_ind][bot]
                    },
                    'R': (self.data['boundary']['rbdy']['variable'][t_ind][left] + self.data['boundary']['rbdy']['variable'][t_ind][right]) * 0.5,
                    'Z': (self.data['boundary']['zbdy']['variable'][t_ind][top] + self.data['boundary']['zbdy']['variable'][t_ind][bot]) * 0.5,
                    'triag': (self.data['boundary']['rbdy']['variable'][t_ind][left] + self.data['boundary']['rbdy']['variable'][t_ind][right] -
                              self.data['boundary']['rbdy']['variable'][t_ind][top] - self.data['boundary']['rbdy']['variable'][t_ind][bot]) /
                             (self.data['boundary']['rbdy']['variable'][t_ind][right] - self.data['boundary']['rbdy']['variable'][t_ind][left]),
                    'elong': (self.data['boundary']['zbdy']['variable'][t_ind][top] - self.data['boundary']['zbdy']['variable'][t_ind][bot]) /
                             (self.data['boundary']['rbdy']['variable'][t_ind][right] - self.data['boundary']['rbdy']['variable'][t_ind][left]),
                    'a': (self.data['boundary']['rbdy']['variable'][t_ind][right] - self.data['boundary']['rbdy']['variable'][t_ind][left]) * 0.5
                }
        return self.calculated[t_ind]
