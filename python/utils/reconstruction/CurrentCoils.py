import json
import math
import os.path

CCM_DB = 'y:/!!!CURRENT_COIL_METHOD/'  # y = \\172.16.12.127

theta_count = 180
gamma_shift = 1
elong_0 = 1.5
shaf_shift = 3
linear_count = 3

def angle(x1, y1, cx, cy):
    val = math.atan2((y1-cy), (x1 - cx))
    if val < 0:
        val += math.tau
    return val


def counterclock(r, z, g_r, g_z):
    count = len(r) // 10
    dir = angle(r[0], z[0], g_r, g_z) - angle(r[count], z[count], g_r, g_z)
    if dir < 0:
        return [v for v in reversed(r)], [v for v in reversed(z)]
    return r, z

def get_integrals(shotn, ts, radius, start, stop):
    with open('%smcc_%d.json' % (CCM_DB, shotn), 'r') as mcc_file:
        data = json.load(mcc_file)
    if data is None:
        return {
            'error': 'No mcc file!'
        }
    timestamps = data['time']['variable']

    res_arr = []
    poly_r = [ts['polys'][poly_ind]['R'] * 0.1 for poly_ind in range(len(ts['polys']))]
    for event_ind in range(len(ts['events'])):
        if start <= ts['events'][event_ind]['timestamp'] <= stop:
            requested_time = ts['events'][event_ind]['timestamp'] * 0.001

            t_ind = 0
            if timestamps[0] > requested_time or requested_time > timestamps[-1]:
                continue
            for t_ind in range(len(timestamps) - 1):
                if timestamps[t_ind] <= requested_time < timestamps[t_ind + 1]:
                    if (requested_time - timestamps[t_ind]) >= (timestamps[t_ind + 1] - requested_time):
                        t_ind += 1
                    break
            body_r, body_z = counterclock(data['boundary']['rbdy']['variable'][t_ind],
                                          data['boundary']['zbdy']['variable'][t_ind],
                                          data['R']['variable'][t_ind],
                                          data['Z']['variable'][t_ind])
            last = {
                'R': body_r,
                'z': body_z
            }
            if data['boundary']['leg_ex']['variable'][t_ind]:
                if isinstance(data['boundary']['rleg_1']['variable'][t_ind], list):
                    last['R'] = [el for el in reversed(data['boundary']['rleg_1']['variable'][t_ind])]
                    last['z'] = [el for el in reversed(data['boundary']['zleg_1']['variable'][t_ind])]

                last['R'].append(data['Rx']['variable'][t_ind])
                last['z'].append(data['Zx']['variable'][t_ind])

                last['R'].extend(body_r)
                last['z'].extend(body_z)

                last['R'].append(data['Rx']['variable'][t_ind])
                last['z'].append(data['Zx']['variable'][t_ind])

                if isinstance(data['boundary']['rleg_2']['variable'][t_ind], list):
                    last['R'].extend(data['boundary']['rleg_2']['variable'][t_ind])
                    last['z'].extend(data['boundary']['zleg_2']['variable'][t_ind])


            z_up = 0
            z_down = 0
            for param_ind in range(len(body_r) - 1):
                if body_r[param_ind] <= \
                        radius < \
                        body_r[param_ind + 1]:
                    z_up = body_z[param_ind] #interpolate

                elif body_r[param_ind + 1] <= \
                        radius < \
                        body_r[param_ind]:
                    z_down = body_z[param_ind] #interpolate

            r_cw = 0
            z_cw = 0
            summ = 0
            for curr_ind in range(int(data['nj']['variable'][t_ind])):
                summ += data['current_coils']['I']['variable'][t_ind][curr_ind]
                r_cw += data['current_coils']['I']['variable'][t_ind][curr_ind] * \
                        data['current_coils']['r']['variable'][t_ind][curr_ind]
                z_cw += data['current_coils']['I']['variable'][t_ind][curr_ind] * \
                        data['current_coils']['z']['variable'][t_ind][curr_ind]

            polys = []
            profile = {
                'val': [],
                'z': [],
                'err': []
            }
            chord_dens = 0
            dens_err = 0
            down_edge = 0
            down_a = 0
            down_b = 0
            up_edge = 0
            up_a = 0
            up_b = 0
            if summ > 0:
                r_cw /= summ
                z_cw /= summ

                #debug
                r_cw = data['R']['variable'][t_ind] + shaf_shift
                z_cw = data['Z']['variable'][t_ind]

                chord = {
                    'up': [],
                    'down': [],
                    'mid': {}
                }

                for poly_ind in range(len(poly_r)):
                    r = poly_r[poly_ind]
                    R = []
                    Z = []

                    dist = math.sqrt(math.pow(r - r_cw, 2) + math.pow(z_cw, 2))
                    a = dist * 0.1

                    while 1:
                        shift = \
                            (r_cw - data['R']['variable'][t_ind]) * \
                            math.pow((1 - math.pow(a / data['a']['variable'][t_ind], 2)), gamma_shift)
                        triang = a * data['de']['variable'][t_ind] / data['a']['variable'][t_ind]
                        elong = elong_0 + a * (data['kx']['variable'][t_ind] - elong_0) / data['a']['variable'][t_ind]
                        if z_cw + a * elong  > 0:
                            theta_start = 0
                            if z_cw <= 0 and r_cw >= r:
                                theta_start = math.pi * 0.5
                            elif z_cw >= 0 and r_cw >= r:
                                theta_start = math.pi
                            elif z_cw >= 0 and r_cw <= r:
                                theta_start = math.pi * 1.5
                            z_prev = z_cw + a * elong * math.sin(theta_start)
                            theta = theta_start
                            for theta_ind in range(theta_count - 1):
                                theta = theta_start + (math.pi * (theta_ind + 1) * 2 / theta_count)
                                z = z_cw + a * elong * math.sin(theta)
                                if z * z_prev <= 0:
                                    theta_prev = theta_start + math.pi * (theta_ind - 1) * 2 / theta_count
                                    theta = -z_prev * (theta - theta_prev) / (z - z_prev)
                                    break
                                z_prev = z
                            r_guess = data['R']['variable'][t_ind] + shift + a * (
                                            math.cos(theta) - triang * math.pow(math.sin(theta), 2))
                            if r_guess >= r:

                                break
                        if a > dist * 2:
                            bad = True
                            break
                        a += dist * 0.001


                    #print(ts['events'][event_ind]['timestamp'], poly_ind, dist, a)

                    shift = \
                        (r_cw - data['R']['variable'][t_ind]) * \
                        math.pow((1 - math.pow(a / data['a']['variable'][t_ind], 2)), gamma_shift)
                    triang = a * data['de']['variable'][t_ind] / data['a']['variable'][t_ind]
                    elong = elong_0 + a * (data['kx']['variable'][t_ind] - elong_0) / data['a']['variable'][t_ind]

                    for theta_ind in range(theta_count + 1):
                        theta = math.pi * theta_ind * 2 / theta_count

                        R.append(
                            data['R']['variable'][t_ind] + shift + a * (
                                        math.cos(theta) - triang * math.pow(math.sin(theta), 2))
                        )
                        Z.append(z_cw + a * elong * math.sin(theta))

                    for i in range(theta_count):
                        if R[i] <= radius < R[i + 1]:
                            chord['down'].append({
                                'poly': poly_ind,
                                'z': Z[i] + (radius - R[i]) * (Z[i + 1] - Z[i]) / (R[i + 1] - R[i])
                            })
                        elif R[i] > radius >= R[i + 1]:
                            chord['up'].append({
                                'poly': poly_ind,
                                'z': Z[i] + (radius - R[i]) * (Z[i + 1] - Z[i]) / (R[i + 1] - R[i])
                            })

                    if r < radius:
                        closest = True
                        for ind_possible in range(len(ts['polys'])):
                            r_possible = poly_r[ind_possible]
                            if radius >= r_possible > r:  # check for bad points
                                closest = False
                                break
                        if closest:
                            chord['mid']['in'] = poly_ind
                    if r > radius:
                        closest = True
                        for ind_possible in range(len(ts['polys'])):
                            r_possible = poly_r[ind_possible]
                            if radius <= r_possible < r:  # check for bad points
                                closest = False
                                break
                        if closest:
                            chord['mid']['out'] = poly_ind
                    polys.append({
                        'r': R,
                        'z': Z,
                        'ind': poly_ind,
                        'a': a
                    })



                points = chord['down']
                points.append({'mid': True})
                points.extend(reversed(chord['up']))
                lost = []
                error = None
                for p_index in range(len(points)):
                    p = points[p_index]
                    if 'mid' in p and p['mid']:
                        if ts['events'][event_ind]['T_e'][chord['mid']['in']]['error'] is not None:
                            error = 'error in middle point "%s"' % \
                                    ts['events'][event_ind]['T_e'][chord['mid']['in']]['error']
                            continue
                        if ts['events'][event_ind]['T_e'][chord['mid']['out']]['error'] is not None:
                            error = 'error in middle point "%s"' % \
                                    ts['events'][event_ind]['T_e'][chord['mid']['out']]['error']
                            continue
                        profile['z'].append(0)
                        t_i = ts['events'][event_ind]['T_e'][chord['mid']['in']]['n']
                        t_o = ts['events'][event_ind]['T_e'][chord['mid']['out']]['n']
                        r_i = poly_r[chord['mid']['in']]
                        r_o = poly_r[chord['mid']['out']]
                        profile['val'].append(t_o + (r_o - radius) * (t_i - t_o) / (r_o - r_i))
                        t_i = ts['events'][event_ind]['T_e'][chord['mid']['in']]['n_err']
                        t_o = ts['events'][event_ind]['T_e'][chord['mid']['out']]['n_err']
                        profile['err'].append(t_o + (r_o - radius) * (t_i - t_o) / (r_o - r_i))
                    else:
                        if ts['events'][event_ind]['T_e'][p['poly']]['error'] is not None:
                            lost.append(p_index)
                            continue
                        profile['z'].append(p['z'])
                        profile['val'].append(ts['events'][event_ind]['T_e'][p['poly']]['n'])
                        profile['err'].append(ts['events'][event_ind]['T_e'][p['poly']]['n_err'])

                for bubble_ind in range(len(profile['z']) - 1):
                    for position_ind in range(bubble_ind + 1, len(profile['z'])):
                        if profile['z'][bubble_ind] > profile['z'][position_ind]:
                            tmp = {
                                'val': profile['val'][bubble_ind],
                                'z': profile['z'][bubble_ind],
                                'err': profile['err'][bubble_ind]
                            }
                            profile['val'][bubble_ind] = profile['val'][position_ind]
                            profile['z'][bubble_ind] = profile['z'][position_ind]
                            profile['err'][bubble_ind] = profile['err'][position_ind]
                            profile['val'][position_ind] = tmp['val']
                            profile['z'][position_ind] = tmp['z']
                            profile['err'][position_ind] = tmp['err']
                for point_ind in range(len(profile['z']) - 1):
                    chord_dens += (profile['val'][point_ind] + profile['val'][point_ind + 1]) * 0.5 * \
                            (profile['z'][point_ind + 1] - profile['z'][point_ind]) * 0.01
                    dens_err += (profile['err'][point_ind] + profile['err'][point_ind + 1]) * 0.5 * \
                            (profile['z'][point_ind + 1] - profile['z'][point_ind]) * 0.01

                if len(profile['z']) > 2 * linear_count:
                    if profile['z'][0] > z_down:
                        s_xy = 0.0
                        s_x = 0.0
                        s_y = 0.0
                        s_x2 = 0.0
                        for ind in range(linear_count):
                            s_x += profile['z'][ind]
                            s_y += profile['val'][ind]
                            s_xy += profile['z'][ind] * profile['val'][ind]
                            s_x2 += profile['z'][ind] * profile['z'][ind]
                        down_a = (linear_count * s_xy - s_x * s_y) / (linear_count * s_x2 - s_x * s_x)
                        down_b = (s_y - down_a * s_x) / linear_count
                        down_edge += (down_a * (z_down + profile['z'][0]) * 0.5 + down_b) * \
                                     (profile['z'][0] - z_down) * 0.01
                    if profile['z'][-1] < z_up:
                        s_xy = 0.0
                        s_x = 0.0
                        s_y = 0.0
                        s_x2 = 0.0
                        for ind in range(len(profile['z']) - 1, len(profile['z']) - 1 - linear_count, -1):
                            s_x += profile['z'][ind]
                            s_y += profile['val'][ind]
                            s_xy += profile['z'][ind] * profile['val'][ind]
                            s_x2 += profile['z'][ind] * profile['z'][ind]
                        up_a = (linear_count * s_xy - s_x * s_y) / (linear_count * s_x2 - s_x * s_x)
                        up_b = (s_y - up_a * s_x) / linear_count
                        up_edge += (up_a * (z_up + profile['z'][-1]) * 0.5 + up_b) * \
                                     (z_up - profile['z'][-1]) * 0.01
                verdict = ''
                if error is not None:
                    verdict = error
                else:
                    if len(lost) > 1:
                        for ind in range(len(lost) - 1):
                            if lost[ind] == lost[ind + 1] + 1 or lost[ind] == lost[ind + 1] - 1:
                                verdict = 'no TS data for 2 neighbour points'
                    if len(lost) / len(points) > 0.3:
                        verdict = 'no TS data in too many points'
            else:
                verdict = 'no plasma'
            #print(timestamps[t_ind], chord_dens, chord_dens + down_edge + up_edge)
            res_arr.append({
                'ind': event_ind,
                'closest_time': timestamps[t_ind] * 1000,
                'last_surf': last,
                'geom_center': {
                    'r': data['R']['variable'][t_ind],
                    'z': data['Z']['variable'][t_ind]
                },
                'coeff': {
                    'r_small': data['a']['variable'][t_ind],
                    'elong': data['kx']['variable'][t_ind],
                    'triang': data['de']['variable'][t_ind]
                },
                'curr_center': {
                    'r': r_cw,
                    'z': z_cw
                },
                'polys': polys,
                'profile': profile,
                'int': chord_dens,
                'int_err': dens_err,
                'z_up': z_up,
                'z_down': z_down,
                'error': verdict,
                'edge': {
                    'down': {
                        'val': down_edge,
                        'a': down_a,
                        'b': down_b
                    },
                    'up': {
                        'val': up_edge,
                        'a': up_a,
                        'b': up_b
                    }
                }
            })
    return {
        'ok': True,
        'data': res_arr
    }


def interpol(x_prev, x, x_next, y_prev, y_next):
    return y_prev + (y_next - y_prev) * (x - x_prev) / (x_next - x_prev)


def linearization(x, y):
    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_x2 = 0
    for i in range(len(x)):
        sum_x += x[i]
        sum_y += y[i]
        sum_xy += x[i] * y[i]
        sum_x2 += math.pow(x[i], 2)
    a = (len(x) * sum_xy - sum_x * sum_y) / (len(x) * sum_x2 - math.pow(sum_x, 2))
    b = (sum_y - a * sum_x) / len(x)
    return a, b


class CCM:
    CCM_DB = 'y:/!!!CURRENT_COIL_METHOD/'  # y = \\172.16.12.127

    theta_count = 180
    gamma_shift = 1
    elong_0 = 1.5
    shaf_shift = 3
    linear_count = 3
    data = {}
    timestamps = []
    error = None

    def set_error(self, err):
        print('Error! \n %s' % err)
        self.error = err

    def __init__(self, shotn):
        filename = '%smcc_%d.json' % (CCM_DB, shotn)
        if not os.path.isfile(filename):
            self.set_error('No mcc file!')
            return
        with open(filename, 'r') as mcc_file:
            self.data = json.load(mcc_file)
        if self.data is None:
            self.set_error('No mcc file!')
            return
        self.timestamps = self.data['time']['variable']

    def counterclock(self, r, z, t_ind):
        g_r = self.data['R']['variable'][t_ind]
        g_z = self.data['Z']['variable'][t_ind]
        count = len(r) // 10
        dir = angle(r[0], z[0], g_r, g_z) - angle(r[count], z[count], g_r, g_z)
        if dir < 0:
            r = [v for v in reversed(r)]
            z = [v for v in reversed(z)]

        for i in range(0, len(r)):
            if r[i] > g_r:
                if z[i - 1] >= g_z > z[i]:
                    if i == 0:
                        return r, z
                    start_ind = i - 1
                    res_r = r[start_ind:]
                    res_r.extend(r[:start_ind])
                    res_z = z[start_ind:]
                    res_z.extend(z[:start_ind])
                    return res_r, res_z
        print('WTF? FIX THIS SHIT')
        return [], []

    def get_surface(self, t_ind, ra=1, theta_count=360):
        sep_r, sep_z = self.counterclock(self.data['boundary']['rbdy']['variable'][t_ind],
                            self.data['boundary']['zbdy']['variable'][t_ind],
                            t_ind)
        if ra == 1:
            return sep_r, sep_z
        if ra > 1 or ra < 0:
            print(ra)
            fuck

        theta_step = (math.tau / theta_count)

        a = ra * (sep_r[0] - self.data['R']['variable'][t_ind])
        triang = a * self.data['de']['variable'][t_ind] / self.data['a']['variable'][t_ind]
        elong = self.elong_0 + \
                a * (self.data['kx']['variable'][t_ind] - self.elong_0) / self.data['a']['variable'][t_ind]
        shift = self.shaf_shift * math.pow((1 - math.pow(a / self.data['a']['variable'][t_ind], 2)), self.gamma_shift)

        r = []
        z = []
        for theta_ind in range(theta_count + 1):
            theta = theta_step * theta_ind
            r.append(self.data['R']['variable'][t_ind] + shift +
                     a * (math.cos(theta) - triang * math.pow(math.sin(theta), 2)))
            z.append(self.data['Z']['variable'][t_ind] + a * elong * math.sin(theta))
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
        sep_r, sep_z = self.counterclock(self.data['boundary']['rbdy']['variable'][t_ind],
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
        center_r = self.data['R']['variable'][t_ind] + self.shaf_shift
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
            'r_min': center_r,
            'r_max': center_r,
            'z': self.data['Z']['variable'][t_ind]
        })
        r_arr = []
        T_arr = []
        n_arr = []
        Te_err = 0
        ne_err = 0
        for i in range(3):
            poly = result[i + 1]
            r_arr.append(poly['a'])
            T_arr.append(poly['Te'])
            n_arr.append(poly['ne'])
            Te_err = max(Te_err, poly['Te_err'])
            ne_err = max(ne_err, poly['ne_err'])
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

