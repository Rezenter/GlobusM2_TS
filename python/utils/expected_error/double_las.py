import math
import phys_const as const
import json

#expected_name = '2021.05.27_1047.6_zs10'
#expected_name = '2021.05.27_1064.4_zs10'

expected_name = {
    '64': '2021.05.27_1064.4',
    '47': '2021.05.27_1047.6'
}

laser_energy = 1  # J
electron_density = 5e19  # local density m-3
abs_calibration = 460600000000000 * 0.125  # value for poly_ind 4
poly_ind = 4
channels = [0, 2, 3, 4]

const_error = 6  # %. Error from APD temperature and spectral calibration
excess_noise = 4
plasma = [50, 100, 300, 600, 900]  # plasma background noise in ph.el

db_path = 'd:/data/db/'
cross_section = (8 * math.pi / 3) * \
                math.pow((math.pow(const.q_e, 2) / (4 * math.pi * const.eps_0 * const.m_e * math.pow(const.c, 2))), 2)

with open('%scalibration/expected/%s.json' % (db_path, expected_name['64']), 'r') as file:
    exp_64 = json.load(file)
with open('%scalibration/expected/%s.json' % (db_path, expected_name['47']), 'r') as file:
    exp_47 = json.load(file)

print('laser_64 = %.1f' % exp_64['lambda_0'])
print('laser_47 = %.1f' % exp_47['lambda_0'])
print('T start = %.1f' % exp_64['T_start'])
print('T stop = %.1f' % exp_64['T_stop'])
print('T mult = %.1f' % exp_64['T_mult'])

with open('out/info_dual.json', 'w') as file:
    json.dump({
        'laser wl 64': exp_64['lambda_0'],
        'laser wl 47': exp_47['lambda_0'],
        'T start': exp_64['T_start'],
        'T stop': exp_64['T_stop'],
        'T mult': exp_64['T_mult'],
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

with open('out/expected_error_dual.csv', 'w') as file:
    header = 'T_e, err, '
    units = 'eV, %, '
    for ch in channels:
        header += 'ch%d, err, ' % (ch + 1)
        units += ' , , '
    file.write(header[:-2] + '\n')
    file.write(units[:-2] + '\n')
    abs_mult = abs_calibration * cross_section * laser_energy * electron_density

    for temp_ind in range(1, len(exp_64['T_arr']) - 1):
        tail = ''
        f_sum = 0
        df_sum = 0
        fdf_sum = 0
        nf_sum = 0
        for ch in channels:
            ph_count_64 = abs_mult * exp_64['poly'][poly_ind]['expected'][ch][temp_ind]
            err_64 = math.sqrt((excess_noise * ph_count_64) + math.pow(plasma[ch], 2) + math.pow(const_error * ph_count_64 * 0.01, 2))
            ph_count_47 = abs_mult * exp_47['poly'][poly_ind]['expected'][ch][temp_ind]
            err_47 = math.sqrt((excess_noise * ph_count_47) + math.pow(plasma[ch], 2) + math.pow(const_error * ph_count_47 * 0.01, 2))

            if ph_count_64 <= 0 or ph_count_47 <= 0:
                tail += '--, --, '
                continue

            f = exp_64['poly'][poly_ind]['expected'][ch][temp_ind] / exp_47['poly'][poly_ind]['expected'][ch][temp_ind]

            der_f = (exp_64['poly'][poly_ind]['expected'][ch][temp_ind + 1] / exp_47['poly'][poly_ind]['expected'][ch][temp_ind + 1] -
                     exp_64['poly'][poly_ind]['expected'][ch][temp_ind - 1] / exp_47['poly'][poly_ind]['expected'][ch][temp_ind - 1]) / \
                    (exp_64['T_arr'][temp_ind + 1] - exp_64['T_arr'][temp_ind - 1])

            err = f * ((err_64 / ph_count_64) + (err_47 / ph_count_47))
            if ch == 2:
                print(f, err_64, ph_count_64, err_47, ph_count_47, err)
            err2 = err * err

            f_sum += math.pow(f, 2) / err2
            df_sum += math.pow(der_f, 2) / err2
            fdf_sum += f * der_f / err2

            tail += '%.3f, %.3f, ' % (f, min(err, 1e100))

        file.write('%.3f, %.3f, %s\n' % (exp_64['T_arr'][temp_ind],
                                         math.sqrt(f_sum / (f_sum * df_sum - math.pow(fdf_sum, 2))) *
                                         100 / exp_64['T_arr'][temp_ind],
                                         tail[:-2]))
print('\nCode OK')
