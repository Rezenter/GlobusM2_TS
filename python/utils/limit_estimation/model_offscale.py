import math
import phys_const as const
import json

abs_path = 'd:/data/db/calibration/abs/processed/'
expected_path = 'd:/data/db/calibration/expected/'
cross_section = (8.0 * math.pi / 3.0) * \
                math.pow((math.pow(const.q_e, 2) / (4 * math.pi * const.eps_0 * const.m_e * math.pow(const.c, 2))), 2)

max_signal = 30000  # ph.el.
abs_filename = '2021.02.03.json'
expected_filename = '2021.02.01.json'
expected_filename = 'expected.json'
poly_ind = 9
laser_energy = 3  # J
gain = 10

geom_coeff = None
with open('%s%s' % (abs_path, abs_filename), 'r') as in_file:
    data = json.load(in_file)
    geom_coeff = data['A']['%s' % poly_ind] * cross_section
    laser_energy *= data['E_mult']
print(geom_coeff)

expected = None
temperatures = None
#with open('%s%s' % (expected_path, expected_filename), 'r') as in_file:
with open('%s' % (expected_filename), 'r') as in_file:
    data = json.load(in_file)
    temperatures = data['T_arr']
    expected = data['poly'][poly_ind]['expected']


with open('offscale_model.csv', 'w') as out:
    out.write('Te, 1, 2, 3, 4, 5\n')
    for t_ind in range(len(temperatures)):
        line = '%.2e, ' % temperatures[t_ind]
        for ch in range(5):
            if expected[ch][t_ind] > 1e-5:
                max_ne = max_signal * gain * 0.1 / (geom_coeff * laser_energy * expected[ch][t_ind])
                line += '%.2e, ' % max_ne
            else:
                line += '--, '
        out.write(line[:-2] + '\n')

print('OK')
