import math
import phys_const as const
import python.utils.reconstruction.CurrentCoils as ccm
import copy

r_step = 0.5  # cm


def interpol(x_prev, x, x_next, y_prev, y_next):
    return y_prev + (y_next - y_prev) * (x - x_prev) / (x_next - x_prev)


class StoredCalculator:
    def __init__(self, shotn, ts_data):
        self.ccm_data = ccm.CCM(shotn)
        self.error = self.ccm_data.error
        if self.error is not None:
            return
        self.ts_data = ts_data
        self.polys = []
        for poly in ts_data['polys']:
            self.polys.append({
                'ind': poly['ind'],
                'R': poly['R'] * 0.1
            })

    def get_profile(self, surfaces, r):
        profile = []
        not_used_surfaces = []
        for surf_ind in range(len(surfaces)):
            surf = surfaces[surf_ind]
            if surf['r_min'] == r == surf['r_max']:
                profile.append({
                    'z': surf['z'],
                    'surf_ind': surf_ind,
                    'Te': surf['Te'],
                    'ne': surf['ne']
                })
            elif surf['r_min'] <= r <= surf['r_max']:
                #print('\n\n----------------')
                #print(surf)
                for index in range(len(surf['r']) - 1):
                    if (surf['r'][index] - r) * (surf['r'][index + 1] - r) <= 0:
                        profile.append({
                            'z': surf['z'][index],
                            'surf_ind': surf_ind,
                            'Te': surf['Te'],
                            'ne': surf['ne']
                        })
            else:
                not_used_surfaces.append(surf_ind)

        return sorted(profile, key=lambda point: point['z'], reverse=True)  # debug
        # unreacheble: Not implemented yet
        fuck

        closest_ind = not_used_surfaces[0]
        for surf_ind in not_used_surfaces:
            if surfaces[surf_ind]['r_min'] - r < surfaces[closest_ind]['r_min'] - r or \
               r - surfaces[surf_ind]['r_max'] < r - surfaces[closest_ind]['r_max']:
                closest_ind = surf_ind

        surf = surfaces[closest_ind]
        if surf['a'] != 0:
            for index in range(len(surf['r']) - 1):
                if (r < surf['r_min'] and surf['r'][index] == surf['r_min']) or \
                        (r > surf['r_max'] and surf['r'][index] == surf['r_max']):
                    profile.append({
                        'z': surf['z'][index],
                        'surf_ind': closest_ind,
                        'val': interpol(),
                        'closest': True
                    })
        else:
            profile.append({
                'z': surf['z'],
                'surf_ind': closest_ind,
                'val': 0,  # interpolated value
                'closest': True
            })

        return sorted(profile, key=lambda point: point['z'], reverse=True)

    def integrate(self, surfaces, nl_r):
        area = 0
        area_w = 0
        volume = 0
        volume_w = 0
        nl_prof = []
        nl_val = 0
        if len(surfaces) != 0:
            left = surfaces[0]['r_min']
            while left < surfaces[0]['r_max']:
                l_prof = self.get_profile(surfaces, left)
                if 0 <= left - nl_r < r_step:
                    nl_prof = l_prof
                    for point_ind in range(len(l_prof) - 1):
                        nl_val += (l_prof[point_ind]['z'] - l_prof[point_ind + 1]['z']) * \
                                  (l_prof[point_ind]['ne'] + l_prof[point_ind + 1]['ne']) * 0.5
                for point_ind in range(len(l_prof) - 1):
                    area += r_step * (l_prof[point_ind]['z'] - l_prof[point_ind + 1]['z'])  # dr*dz
                    area_w += r_step * (l_prof[point_ind]['z'] - l_prof[point_ind + 1]['z']) * \
                              (l_prof[point_ind]['ne'] + l_prof[point_ind + 1]['ne']) * 0.5 * \
                              (l_prof[point_ind]['Te'] + l_prof[point_ind + 1]['Te']) * 0.5
                    volume += r_step * (l_prof[point_ind]['z'] - l_prof[point_ind + 1]['z']) * math.tau * left
                    volume_w += r_step * (l_prof[point_ind]['z'] - l_prof[point_ind + 1]['z']) * \
                                (l_prof[point_ind]['ne'] + l_prof[point_ind + 1]['ne']) * 0.5 * \
                                (l_prof[point_ind]['Te'] + l_prof[point_ind + 1]['Te']) * 0.5 * \
                                math.tau * left
                left += r_step
                #fuck
        return area * 1e-4, area_w * 1e-4 * const.q_e, volume * 1e-6, volume_w * 1e-6 * const.q_e, nl_prof, nl_val * 1e-2

    def calc_laser_shot(self, requested_time, nl_r):
        t_ind = 0
        for t_ind in range(len(self.ccm_data.timestamps) - 1):
            if self.ccm_data.timestamps[t_ind] <= requested_time < self.ccm_data.timestamps[t_ind + 1]:
                if (requested_time - self.ccm_data.timestamps[t_ind]) >= (self.ccm_data.timestamps[t_ind + 1] - requested_time):
                    t_ind += 1
                break
        poly_a = self.ccm_data.find_poly(self.polys, t_ind)
        #for poly in poly_a:
        #    print(poly['a'], poly['Te'], poly['ne'])
        for poly in poly_a:
            if poly['a'] == 0:
                continue
            poly['r_min'] = 60
            poly['r_max'] = 20
            for point in poly['r']:
                poly['r_min'] = min(poly['r_min'], point)
                poly['r_max'] = max(poly['r_max'], point)

        area, area_w, volume, volume_w, nl_profile, nl_val = self.integrate(poly_a, nl_r)
        return {
            'area': area,
            'area_w': area_w,
            'vol': volume,
            'vol_w': volume_w,
            'surfaces': poly_a,
            'nl_profile': nl_profile,
            'nl': nl_val
        }

    def calc_dynamics(self, t_from, t_to, nl_r):
        print('calc dynamics')
        result = []
        for event_ind in range(len(self.ts_data['events'])):
            event = self.ts_data['events'][event_ind]
            if t_from <= event['timestamp'] <= t_to:
                if event['error'] is not None:
                    print('Laser shot %d = %.1fs skip due to error in ts_data: %s' %
                          (event_ind, event['timestamp'], event['error']))
                    continue
                if not self.ccm_data.timestamps[0] <= event['timestamp'] * 0.001 <= self.ccm_data.timestamps[-1]:
                    print('No ccm data for laser shot %d = %.1fs' % (event_ind, event['timestamp']))
                    continue
                #print('Process event laser shot %d = %.1fs' % (event_ind, event['timestamp']))
                for poly in self.polys:
                    if event['T_e'][poly['ind']]['error']:
                        poly['skip'] = True
                        poly['Te'] = None
                        poly['ne'] = None
                        continue
                    poly['skip'] = False
                    poly['Te'] = event['T_e'][poly['ind']]['T']
                    poly['ne'] = event['T_e'][poly['ind']]['n']
                result.append({
                    'event_index': event_ind,
                    'data': copy.deepcopy(self.calc_laser_shot(event['timestamp'] * 0.001, nl_r))
                })
        return {
            'ok': True,
            'data': result
        }
