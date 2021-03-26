import math
import CurrentCoils as ccm

profile = [
    {
        'r/a': 0.0,
        'Te': 714,
        'ne': 2.91E19
    }, {
        'r/a': 0.01005,
        'Te': 705,
        'ne': 2.98E19
    }, {
        'r/a': 0.09045,
        'Te': 730,
        'ne':2.92E19
    }, {
        'r/a': 0.1156,
        'Te': 709,
        'ne': 2.98E19
    }, {
        'r/a': 0.201,
        'Te': 736,
        'ne': 2.98E19
    }, {
        'r/a': 0.3216,
        'Te': 753,
        'ne': 3.09E19
    }, {
        'r/a': 0.4372,
        'Te': 749,
        'ne': 3.07E19
    }, {
        'r/a': 0.5578,
        'Te': 583,
        'ne': 2.57E19
    }, {
        'r/a': 0.6834,
        'Te': 395,
        'ne': 1.94E19
    }, {
        'r/a': 0.7839,
        'Te': 229,
        'ne': 1.55E19
    }, {
        'r/a': 0.8392,
        'Te': 186,
        'ne': 1.23E19
    }, {
        'r/a': 1,
        'Te': 60,
        'ne': 1e19
    }
]  # start
profile = [
    {
        'r/a': 0.0,
        'Te': 907,
        'ne': 3.96E19
    }, {
        'r/a': 0.01005,
        'Te': 920,
        'ne': 3.99E19
    }, {
        'r/a': 0.09045,
        'Te': 878,
        'ne': 3.78E19
    }, {
        'r/a': 0.1156,
        'Te': 896,
        'ne': 3.6E19
    }, {
        'r/a': 0.201,
        'Te': 876,
        'ne': 3.6E19
    }, {
        'r/a': 0.3216,
        'Te': 837,
        'ne': 3.55E19
    }, {
        'r/a': 0.4372,
        'Te': 762,
        'ne': 3.12E19
    }, {
        'r/a': 0.5578,
        'Te': 566,
        'ne': 2.7E19
    }, {
        'r/a': 0.6834,
        'Te': 315,
        'ne': 1.85E19
    }, {
        'r/a': 0.7839,
        'Te': 198,
        'ne': 1.43E19
    }, {
        'r/a': 0.8392,
        'Te': 138,
        'ne': 1.23E19
    }, {
        'r/a': 1,
        'Te': 60,
        'ne': 1e19
    }
]  # end
shotn = 39627
requested_time = 194.7 * 0.001  # start
requested_time = 203.8 * 0.001  # stop

theta_step = 0.2 * math.pi / 180  # rad
ra_step = 0.01  # cm
ra_center = 0.001  # 1


def interpol(x_prev, x, x_next, y_prev, y_next):
    return y_prev + (y_next - y_prev) * (x - x_prev) / (x_next - x_prev)


def integrate_ring(inner, outer):
    t_integral = 0
    t_area = 0
    t_volume = 0
    c_r = (inner['r'][0] + outer['r'][0]) * 0.5
    central = interpol(inner['r'][0], c_r, outer['r'][0], inner['val']['nT'], outer['val']['nT'])
    for i in range(-1, len(inner['r']) - 1):
        l1 = math.sqrt(math.pow(inner['r'][i] - outer['r'][i], 2) +
                       math.pow(inner['z'][i] - outer['z'][i], 2))
        l3 = math.sqrt(math.pow(inner['r'][i + 1] - outer['r'][i + 1], 2) +
                       math.pow(inner['z'][i + 1] - outer['z'][i + 1], 2))
        l_radial = (l1 + l3) * 0.5
        l2 = math.sqrt(math.pow(inner['r'][i + 1] - inner['r'][i], 2) +
                       math.pow(inner['z'][i + 1] - inner['z'][i], 2))
        l4 = math.sqrt(math.pow(outer['r'][i + 1] - outer['r'][i], 2) +
                       math.pow(outer['z'][i + 1] - outer['z'][i], 2))
        l_angular = (l2 + l4) * 0.5
        area = l_angular * l_radial
        volume = area * math.pi * (2 * inner['r'][i] + l_radial)
        t_integral += central * volume
        t_area += area
        t_volume += volume
    if t_integral < 0:
        fuck
    return t_integral, t_area, t_volume


def interpolate_profile(ra):
    if ra == 1:
        return {
                'T': profile[-1]['Te'],
                'n': profile[-1]['ne'],
                'nT': profile[-1]['Te'] * profile[-1]['ne']
            }
    for ind in range(1, len(profile)):
        if profile[ind - 1]['r/a'] <= ra < profile[ind]['r/a']:
            Te = interpol(profile[ind - 1]['r/a'], ra, profile[ind]['r/a'], profile[ind - 1]['Te'], profile[ind]['Te'])
            ne = interpol(profile[ind - 1]['r/a'], ra, profile[ind]['r/a'], profile[ind - 1]['ne'], profile[ind]['ne'])
            res = {
                'T': Te,
                'n': ne,
                'nT': Te * ne
            }
            return res
    fuck


for point in profile:
    point['val'] = point['Te'] * point['ne']

ccm_data = ccm.CCM(shotn)

t_ind = 0
if ccm_data.timestamps[0] > requested_time or requested_time > ccm_data.timestamps[-1]:
    fuck
for t_ind in range(len(ccm_data.timestamps) - 1):
    if ccm_data.timestamps[t_ind] <= requested_time < ccm_data.timestamps[t_ind + 1]:
        if (requested_time - ccm_data.timestamps[t_ind]) >= (ccm_data.timestamps[t_ind + 1] - requested_time):
            t_ind += 1
        break

sep_r, sep_z = ccm_data.get_surface(t_ind)

for i in range(len(sep_r)):
    print(sep_z[i], sep_r[i])
fuck

a0 = sep_r[0] - ccm_data.data['R']['variable'][t_ind]

surfaces = []

integral = 0
area_int = 0
volume_int = 0
ra = ra_center
r, z = ccm_data.get_surface(t_ind, ra=ra, theta_step=theta_step)
inner_data = {
    'r': r,
    'z': z,
    'ra': ra,
    'val': interpolate_profile(ra)
}
#central_area =
surfaces.append(inner_data)
while inner_data['ra'] + ra_step < 1:
    outer_ra = inner_data['ra'] + ra_step
    r, z = ccm_data.get_surface(t_ind, ra=outer_ra, theta_step=theta_step)
    outer_data = {
        'r': r,
        'z': z,
        'ra': outer_ra,
        'val': interpolate_profile(outer_ra)
    }
    integr, are, vol = integrate_ring(inner_data, outer_data)
    integral += integr
    area_int += are
    volume_int += vol
    inner_data = outer_data
    surfaces.append(inner_data)
#integrate outer

print(integral * 1.6e-19 * 1e-6 * 1e-3, area_int * 1e-4, volume_int * 1e-6)

with open('surf.csv', 'w') as out_fp:
    line = 'theta, '
    for surf in surfaces:
        line += 'R %.3f, Z %.3f, ' % (surf['ra'], surf['ra'])
    out_fp.write(line[:-2] + '\n')
    i = 0
    while i * theta_step < math.tau:
        line = '%.2f, ' % (i * theta_step * 180 / math.pi)
        for surf in surfaces:
            line += '%.3f, %.3f, ' % (surf['r'][i], surf['z'][i])
        out_fp.write(line[:-2] + '\n')
        i += 1

with open('xyz_te.csv', 'w') as out_fp:
    line = 'R, Z, Te\n'
    out_fp.write(line)
    i = 0
    while i * theta_step < math.tau:
        for surf in surfaces:
            out_fp.write('%.3f, %.3f, %.1f\n' % (surf['r'][i], surf['z'][i], surf['val']['T']))
        i += 1

with open('xyz_ne.csv', 'w') as out_fp:
    line = 'R, Z, ne\n'
    out_fp.write(line)
    i = 0
    while i * theta_step < math.tau:
        for surf in surfaces:
            out_fp.write('%.3f, %.3f, %.1f\n' % (surf['r'][i], surf['z'][i], surf['val']['n']))
        i += 1

with open('xyz_nete.csv', 'w') as out_fp:
    line = 'R, Z, nete\n'
    out_fp.write(line)
    i = 0
    while i * theta_step < math.tau:
        for surf in surfaces:
            out_fp.write('%.3f, %.3f, %.1f\n' % (surf['r'][i], surf['z'][i], surf['val']['nT']))
        i += 1
print('OK')
