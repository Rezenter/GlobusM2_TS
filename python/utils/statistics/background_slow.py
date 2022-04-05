import shtRipper

db_path = 'in/slow/'

plasma_current_threshold = 290000 # A, filter points with Ip > threshold
ch_width = [12.6, 24.55, 48.52, 96.56, 192.91]
gain = [64, 32, 16, 8, 8]
t_start = 150
poly = 9
shotn = 41527

with open('out/background_slow.csv', 'w') as out_file:
    sht_name = 'Z:/sht%d.SHT' % shotn
    plasma_curr = shtRipper.ripper.read(sht_name)['Ip внутр.(Пр2ВК) (инт.18)']

    header = ''
    files = []
    for ch in range(5):
        header += 'norm_Noise_%d, ' % (ch + 1)
        with open('%ssht%d/%d_process_ADC_ch%d_data.txt' % (db_path, shotn, shotn, ch + 1), 'r') as file:
            data = []
            flattop = False
            t_ind = 0
            file.readline()
            zero = 0
            count = 0
            for in_line in file:
                cols = in_line.split(',')
                time = float(cols[0])
                if time < 50:
                    zero += float(cols[poly + 1])/gain[ch]
                    count += 1
                if time < t_start:
                    continue
                while plasma_curr['x'][t_ind] * 1000 < time:
                    t_ind += 1
                current = plasma_curr['y'][t_ind]
                if current < plasma_current_threshold * 0.95:
                    if flattop:
                        break
                    continue
                if current >= plasma_current_threshold:
                    flattop = True
                data.append(float(cols[poly + 1])/gain[ch] - zero / count)
            files.append(data)
    for ch in range(2, 5):
        header += 'noiseExcess_%d, ' % (ch + 1)
    out_file.write(header[:-2] + '\n')

    for event_ind in range(len(files[0])):
        line = ''
        for ch in range(5):
            line += '%.4e, ' % (files[ch][event_ind] / ch_width[ch])
        background = (files[0][event_ind] / ch_width[0] + files[1][event_ind] / ch_width[1]) * 0.5
        for ch in range(2, 5):
            line += '%.4e, ' % (files[ch][event_ind] / (ch_width[ch] * background))

        out_file.write(line[:-2] + '\n')

print('OK')
