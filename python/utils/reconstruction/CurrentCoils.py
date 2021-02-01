import json
import math

CCM_DB = 'y:/!!!CURRENT_COIL_METHOD/'  # y = \\172.16.12.127

theta_count = 180
gamma_shift = 1


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
            last = {
                'R': data['boundary']['rbdy']['variable'][t_ind],
                'z': data['boundary']['zbdy']['variable'][t_ind]
            }
            if data['boundary']['leg_ex']['variable'][t_ind]:
                last['R'] = [el for el in reversed(data['boundary']['rleg_1']['variable'][t_ind])]
                last['z'] = [el for el in reversed(data['boundary']['zleg_1']['variable'][t_ind])]

                last['R'].append(data['Rx']['variable'][t_ind])
                last['z'].append(data['Zx']['variable'][t_ind])

                last['R'].extend(data['boundary']['rbdy']['variable'][t_ind])
                last['z'].extend(data['boundary']['zbdy']['variable'][t_ind])

                last['R'].append(data['Rx']['variable'][t_ind])
                last['z'].append(data['Zx']['variable'][t_ind])

                last['R'].extend(data['boundary']['rleg_2']['variable'][t_ind])
                last['z'].extend(data['boundary']['zleg_2']['variable'][t_ind])
            else:
                last['R'] = data['boundary']['rbdy']['variable'][t_ind]
                last['z'] = data['boundary']['zbdy']['variable'][t_ind]

            z_up = 0
            z_down = 0
            for param_ind in range(len(data['boundary']['rbdy']['variable'][t_ind]) - 1):
                if data['boundary']['rbdy']['variable'][t_ind][param_ind] <= \
                        radius < \
                        data['boundary']['rbdy']['variable'][t_ind][param_ind + 1]:
                    z_up = data['boundary']['zbdy']['variable'][t_ind][param_ind] #interpolate
                elif data['boundary']['rbdy']['variable'][t_ind][param_ind + 1] <= \
                        radius < \
                        data['boundary']['rbdy']['variable'][t_ind][param_ind]:
                    z_down = data['boundary']['zbdy']['variable'][t_ind][param_ind] #interpolate
            # dick move
            z_up = math.fabs(z_up)
            z_down = math.fabs(z_down)
            #print(z_up + z_down)

            r_cw = 0
            z_cw = 0
            summ = 0
            for curr_ind in range(int(data['nj']['variable'][t_ind])):
                summ += data['current_coils']['I']['variable'][t_ind][curr_ind]
                r_cw += data['current_coils']['I']['variable'][t_ind][curr_ind] * \
                        data['current_coils']['r']['variable'][t_ind][curr_ind]
                z_cw += data['current_coils']['I']['variable'][t_ind][curr_ind] * \
                        data['current_coils']['z']['variable'][t_ind][curr_ind]
            r_cw /= summ
            z_cw /= summ

            chord = {
                'up': [],
                'down': [],
                'mid': {}
            }

            polys = []
            for poly_ind in range(len(poly_r)):
                r = poly_r[poly_ind]
                R = []
                Z = []

                a = math.sqrt(math.pow(z_cw, 2) + math.pow(r - r_cw, 2))
                shift = \
                    (r_cw - data['R']['variable'][t_ind]) * \
                    math.pow((1 - math.pow(a / data['a']['variable'][t_ind], 2)), gamma_shift)
                triang = a * data['de']['variable'][t_ind] / data['a']['variable'][t_ind]
                elong = 1 + a * (data['kx']['variable'][t_ind] - 1) / data['a']['variable'][t_ind]

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
                    'ind': poly_ind
                })

            profile = {
                'val': [],
                'z': [],
                'err': []
            }

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

            chord_dens = 0
            dens_err = 0
            for point_ind in range(len(profile['z']) - 1):
                chord_dens += (profile['val'][point_ind] + profile['val'][point_ind + 1]) * 0.5 * \
                        (profile['z'][point_ind + 1] - profile['z'][point_ind]) * 0.01
                dens_err += (profile['err'][point_ind] + profile['err'][point_ind + 1]) * 0.5 * \
                        (profile['z'][point_ind + 1] - profile['z'][point_ind]) * 0.01
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
                'error': verdict
            })
    return {
        'ok': True,
        'data': res_arr
    }


