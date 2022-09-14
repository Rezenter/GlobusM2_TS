import math
import phys_const as const
import json

expected_name = '2021.05.27_1047.6_zs10'
expected_name = '2021.05.27_1064.4_zs10'
expected_name = '2021.05.27_1047.6'
expected_name = '2022.09.01'
#expected_name = '2021.05.27_1064.4'


laser_wl = 1064.5
laser_energy = 1.9  # J
electron_density = 5e19  # local density m-3
abs_calibration = 460600000000000 * 0.125  # value for poly_ind 4
poly_ind = 1
channels = [0, 1, 2, 3, 4]

const_error = 6  # %. Error from APD temperature and spectral calibration
excess_noise = 4
plasma = [50, 100, 300, 600, 900]  # plasma background noise in ph.el

db_path = 'd:/data/db/'
cross_section = (8 * math.pi / 3) * \
                math.pow((math.pow(const.q_e, 2) / (4 * math.pi * const.eps_0 * const.m_e * math.pow(const.c, 2))), 2)

with open('%scalibration/expected/%s.json' % (db_path, expected_name), 'r') as file:
    expected = json.load(file)

print('laser = %.1f' % laser_wl)
print('T start = %.1f' % expected['Te_low'])
print('T stop = %.1f' % expected['Te_high'])
print('T mult = %.1f' % expected['Te_mult'])

with open('out/info_%s.json' % expected_name, 'w') as file:
    json.dump({
        'laser wl': laser_wl,
        'T start': expected['Te_low'],
        'T stop': expected['Te_high'],
        'T mult': expected['Te_mult'],
        'expected name': expected_name,
        'laser energy': laser_energy,
        'n_e': '%.1e' % electron_density,
        'abs_mult': '%.2e' % abs_calibration,
        'poly_ind': poly_ind,
        'channels': channels,
        'noise': {
            'const error': const_error,
            'excess noise': excess_noise,
            'plasma noise': plasma
        },
        'TS crosssection': '%.2e' % cross_section
    }, file)

with open('out/expected_error_%s.csv' % expected_name, 'w') as file:
    header = 'T_e, err, '
    units = 'eV, %, '
    for ch in channels:
        header += 'ch%d, err, ' % (ch + 1)
        units += 'ph.el., ph.el, '
    file.write(header[:-2] + '\n')
    file.write(units[:-2] + '\n')
    abs_mult = abs_calibration * cross_section * laser_energy * electron_density

    for temp_ind in range(1, len(expected['T_arr']) - 1):


        tail = ''
        f_sum = 0
        df_sum = 0
        fdf_sum = 0
        for ch in channels:
            f = expected['poly'][poly_ind]['expected'][ch][temp_ind]
            der_f = (expected['poly'][poly_ind]['expected'][ch][temp_ind + 1] - expected['poly'][poly_ind]['expected'][ch][temp_ind - 1]) / \
                    (expected['T_arr'][temp_ind + 1] - expected['T_arr'][temp_ind - 1])
            ph_count = abs_mult * f

            err2 = (excess_noise * ph_count) + math.pow(plasma[ch], 2) + math.pow(const_error * ph_count * 0.01, 2)

            f_sum += math.pow(f, 2) / err2
            df_sum += math.pow(der_f, 2) / err2
            fdf_sum += f * der_f / err2
            tail += '%.1f, %.1f, ' % (ph_count, math.sqrt(err2))

        file.write('%.1f, %.1f, %s\n' % (expected['T_arr'][temp_ind],
                                         math.sqrt(math.pow(abs_mult, -2) * f_sum / (f_sum * df_sum - math.pow(fdf_sum, 2))) *
                                         100 / expected['T_arr'][temp_ind],
                                         tail[:-2]))
print('\nCode OK')
