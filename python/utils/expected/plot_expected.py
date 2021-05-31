import json

db_path = 'd:/data/db/calibration/expected/'

expected_name_64 = '2021.05.27_1064.4_zs10'
expected_name_47 = '2021.05.27_1047.6_zs10'

expected_name_64 = '2021.05.27_1064.4'
expected_name_47 = '2021.05.27_1047.6'

with open('%s%s.json' % (db_path, expected_name_64), 'r') as file:
    expected_64 = json.load(file)
with open('%s%s.json' % (db_path, expected_name_47), 'r') as file:
    expected_47 = json.load(file)
for poly in range(10):
    with open('out/expected_p%d.csv' % poly, 'w') as file:
        header = 'Te, '
        units = 'eV, '
        for ch in range(5):
            header += '64_ch%d, ' % (ch + 1)
            units += ' a.u., '
        for ch in range(5):
            header += '47_ch%d, ' % (ch + 1)
            units += ' a.u., '
        for ch in range(5):
            header += 'rel_ch%d, ' % (ch + 1)
            units += ' a.u., '
        file.write(header[:-2] + '\n')
        file.write(units[:-2] + '\n')

        for wl_ind in range(len(expected_64['T_arr'])):
            line = '%.1f, ' % expected_64['T_arr'][wl_ind]
            for ch in range(5):
                line += '%.4f, ' % (expected_64['poly'][poly]['expected'][ch][wl_ind])
            for ch in range(5):
                line += '%.4f, ' % (expected_47['poly'][poly]['expected'][ch][wl_ind])
            for ch in range(5):
                if expected_47['poly'][poly]['expected'][ch][wl_ind] <= 0:
                    val = 1e100
                else:
                    val = expected_64['poly'][poly]['expected'][ch][wl_ind] / \
                          expected_47['poly'][poly]['expected'][ch][wl_ind]
                line += '%.4f, ' % val
            file.write(line[:-2] + '\n')

print('Code OK')
