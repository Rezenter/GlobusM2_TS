import json
import statistics

r_bin_count = 40

normalised = {
    'points': [],
    'averaged': [{
        'bin': bin_i,
        'R_low': -21 + bin_i * (2.5 + 21)/r_bin_count,
        'R_high': -21 + (bin_i + 1) * (2.5 + 21)/r_bin_count,
        'points': [],
        'Te': {
            'mean': 0.0,
            'std': 0.0,
            'mape': 0.0
        },
        'ne': {
            'mean': 0.0,
            'std': 0.0,
            'mape': 0.0
        }

    } for bin_i in range(r_bin_count)]
}

with open('out/normalised.json', 'r') as file:
    normalised['points'] = json.load(file)

'''
shotn = 0
time = 0
shot_count = 0
time_count = 0
for point in normalised['points']:
    if shotn != point['shotn']:
        shot_count += 1
        time_count += 1
        shotn = point['shotn']
        time = point['time']
    elif time != point['time']:
            time_count += 1
            time = point['time']

print(shot_count, time_count)
fuck'''

for point_ind in range(len(normalised['points'])):
    if normalised['points'][point_ind]['before sawtooth #'] == 1:
        for bin in normalised['averaged']:
            if bin['R_low'] <= normalised['points'][point_ind]['R-R_lcfs'] < bin['R_high']:
                bin['points'].append(point_ind)
                break


te_mape_arr_all = 0.0
ne_mape_arr_all = 0.0
length = 0

for bin in normalised['averaged']:
    te = []
    ne = []
    for p in bin['points']:
        te.append(normalised['points'][p]['T_e/<Te>'])
        ne.append(normalised['points'][p]['n_e/<ne>'])
    if len(te) >= 2:
        bin['Te']['mean'] = statistics.fmean(te)
        bin['Te']['std'] = statistics.stdev(te)

        bin['ne']['mean'] = statistics.fmean(ne)
        bin['ne']['std'] = statistics.stdev(ne)

        for p in bin['points']:
            te_mape_arr = [abs(v - bin['Te']['mean'])/bin['Te']['mean'] for v in te]
            ne_mape_arr = [abs(v - bin['ne']['mean'])/bin['ne']['mean'] for v in ne]
            bin['Te']['mape'] = 100 * sum(te_mape_arr) / len(te_mape_arr)
            bin['ne']['mape'] = 100 * sum(ne_mape_arr) / len(ne_mape_arr)

            te_mape_arr_all += sum(te_mape_arr)
            ne_mape_arr_all += sum(ne_mape_arr)
            length += len(te_mape_arr)

        print((bin['R_high'] + bin['R_low']) * 0.5, bin['Te']['mean'], bin['Te']['std'], bin['ne']['mean'], bin['ne']['std'], bin['Te']['mape'], bin['ne']['mape'])
    #calc mape

mape_te = 100 * te_mape_arr_all / length
mape_ne = 100 * ne_mape_arr_all / length

print('\n\n', mape_te, mape_ne)

print('\n\nCode OK')