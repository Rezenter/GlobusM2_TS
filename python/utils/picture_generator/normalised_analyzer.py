import json
import statistics
import math

#r_bin_count = 22
r_bin_count = 16

normalised = {
    'points': [],
    'averaged': [{
        'bin': bin_i,
        'R_low': -19.5 + bin_i * (2.5 + 19.5)/r_bin_count,
        'R_high': -19.5 + (bin_i + 1) * (2.5 + 19.5)/r_bin_count,
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


normalised = {
    'points': [],
    'averaged': [{
        'bin': bin_i,
        'R_low': -5 + bin_i * (2.03 + 5)/r_bin_count,
        'R_high': -5 + (bin_i + 1) * (2.03 + 5)/r_bin_count,
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

'''
with open('out/normalised.json', 'r') as file:
    normalised['points'] = json.load(file)
'''


with open('in/normalised_after.csv', 'r') as file:
    te_ind = 3
    ne_ind = 4
    before_ind = 24
    after_ind = 25

    r_ind = before_ind
    #r_ind = after_ind
    r_ind = 2
    for line in file:
        spl = line.split(',')
        try:
            normalised['points'].append({
                'R-R_lcfs': float(spl[r_ind]),
                'n_e/<ne>': float(spl[ne_ind]),
                'T_e/<Te>': float(spl[te_ind])
            })
        except ValueError:
            pass


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

print("counters: ", shot_count, time_count, '\n')
'''


mape_arr_tene = []
count = 0
for point_ind in range(len(normalised['points'])):
    if 1 or normalised['points'][point_ind]['before sawtooth #'] >= 3:
        count += 1
        if 0 and -9 < normalised['points'][point_ind]['R-R_lcfs'] < -1.5:
            expected = 0.87441 * math.pow(normalised['points'][point_ind]['n_e/<ne>'], 1.76595)
            mape_arr_tene.append(abs(expected - normalised['points'][point_ind]['T_e/<Te>'])/expected)

        for bin in normalised['averaged']:
            if bin['R_low'] <= normalised['points'][point_ind]['R-R_lcfs'] < bin['R_high']:
                bin['points'].append(point_ind)
                break
#print("MAPE to average: ", 100 * sum(mape_arr_tene) / len(mape_arr_tene), len(mape_arr_tene), count)
#fuck


te_mape_arr_all = 0.0
ne_mape_arr_all = 0.0
length = 0

for bin_ind in range(len(normalised['averaged'])):
    bin = normalised['averaged'][bin_ind]

    te = []
    ne = []
    for p in bin['points']:
        te.append(normalised['points'][p]['T_e/<Te>'])
        ne.append(normalised['points'][p]['n_e/<ne>'])
    if len(te) >= 2:
        bin['Te']['mean'] = statistics.fmean(te)
        bin['Te']['std'] = statistics.stdev(te)
        bin['Te']['err'] = bin['Te']['std'] / math.sqrt(len(te))


        bin['ne']['mean'] = statistics.fmean(ne)
        bin['ne']['std'] = statistics.stdev(ne)
        bin['ne']['err'] = bin['ne']['std'] / math.sqrt(len(ne))

        if bin_ind > 0:
            te_mape_arr = []
            ne_mape_arr = []

            for p in bin['points']:
                te_ave = normalised['averaged'][bin_ind - 1]['Te']['mean'] + (normalised['averaged'][bin_ind]['Te']['mean'] - normalised['averaged'][bin_ind - 1]['Te']['mean'])*(normalised['points'][p]['R-R_lcfs'] - (normalised['averaged'][bin_ind - 1]['R_high'] + normalised['averaged'][bin_ind - 1]['R_low']) * 0.5)/((normalised['averaged'][bin_ind]['R_high'] + normalised['averaged'][bin_ind]['R_low']) * 0.5 - (normalised['averaged'][bin_ind - 1]['R_high'] + normalised['averaged'][bin_ind - 1]['R_low']) * 0.5)
                ne_ave = normalised['averaged'][bin_ind - 1]['ne']['mean'] + (normalised['averaged'][bin_ind]['ne']['mean'] - normalised['averaged'][bin_ind - 1]['ne']['mean'])*(normalised['points'][p]['R-R_lcfs'] - (normalised['averaged'][bin_ind - 1]['R_high'] + normalised['averaged'][bin_ind - 1]['R_low']) * 0.5)/((normalised['averaged'][bin_ind]['R_high'] + normalised['averaged'][bin_ind]['R_low']) * 0.5 - (normalised['averaged'][bin_ind - 1]['R_high'] + normalised['averaged'][bin_ind - 1]['R_low']) * 0.5)

                te_mape_arr.append(abs(normalised['points'][p]['T_e/<Te>'] - te_ave)/te_ave)
                ne_mape_arr.append(abs(normalised['points'][p]['n_e/<ne>'] - ne_ave)/ne_ave)

                '''
                te_mape_arr = [abs(v - bin['Te']['mean'])/bin['Te']['mean'] for v in te]
                ne_mape_arr = [abs(v - bin['ne']['mean'])/bin['ne']['mean'] for v in ne]
                '''

            bin['Te']['mape'] = 100 * sum(te_mape_arr) / len(te_mape_arr)
            bin['ne']['mape'] = 100 * sum(ne_mape_arr) / len(ne_mape_arr)

            te_mape_arr_all += sum(te_mape_arr)
            ne_mape_arr_all += sum(ne_mape_arr)
            length += len(te_mape_arr)

        print((bin['R_high'] + bin['R_low']) * 0.5, bin['Te']['mean'], bin['Te']['err'], bin['ne']['mean'], bin['ne']['err'])
    #calc mape

mape_te = 100 * te_mape_arr_all / length
mape_ne = 100 * ne_mape_arr_all / length

print('\n\nMAPE to function: ', mape_te, mape_ne)

print('\n\nCode OK')