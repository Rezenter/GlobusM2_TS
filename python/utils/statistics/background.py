import os
import json
import shtRipper

db_path = 'in/high/'
files = os.listdir(db_path)

plasma_current_threshold = 390000 # A, filter points with Ip > threshold
t_start = 150 # ms
ch_width = [12.6, 24.55, 48.52, 96.56, 192.91]
poly = 9

with open('out/background.csv', 'w') as out_file:
    header = 'shotn, time, '
    for ch in range(5):
        header += 'norm_Noise_%d, ' % (ch + 1)
    for ch in range(2, 5):
        header += 'noiseExcess_%d, ' % (ch + 1)
    out_file.write(header[:-2] + '\n')
    for file_name in files:
        if not file_name.endswith('.json'):
            continue
        sht_name = 'Z:/sht%s.SHT' % file_name[:5]
        plasma_curr = shtRipper.ripper.read(sht_name)['Ip внутр.(Пр2ВК) (инт.18)']

        with open('%s%s' % (db_path, file_name), 'r') as file:
            data = json.load(file)['data']
            flattop = False
            t_ind = 0
            for event in data:
                if event['timestamp'] < t_start:
                    continue
                while plasma_curr['x'][t_ind] * 1000 < event['timestamp']:
                    t_ind += 1
                current = plasma_curr['y'][t_ind]
                if current < plasma_current_threshold:
                    if flattop:
                        break
                    continue
                flattop = True
                if event['error'] is not None:
                    continue
                line = '%s, %.2f, ' % (file_name[:5], event['timestamp'])

                for ch in range(5):
                    line += '%.2e, ' % (pow(event['poly']['%d' % poly]['ch'][ch]['pre_std'], 2) / ch_width[ch])
                background = (pow(event['poly']['%d' % poly]['ch'][0]['pre_std'], 2) / ch_width[0] + pow(event['poly']['%d' % poly]['ch'][1]['pre_std'], 2) / ch_width[1]) * 0.5
                for ch in range(2, 5):
                    line += '%.2e, ' % (pow(event['poly']['%d' % poly]['ch'][ch]['pre_std'], 2) / (ch_width[ch] * background))

                print(line[:-2])
                out_file.write(line[:-2] + '\n')
        #break # for debug
print('OK')
