import json
import math

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
            print(timestamps[t_ind], chord_dens, chord_dens + down_edge + up_edge)
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


