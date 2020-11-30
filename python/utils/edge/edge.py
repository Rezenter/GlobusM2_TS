import json

db_path = 'd:/data/db/plasma/result/'

shotn_table = {
    355: 39586,
    358: 39589,
    359: 39590
}

shotn = 355
polys = [
    {
        'ind': 0,
        'R': 580.5
    },
    {
        'ind': 1,
        'R': 570
    },
    {
        'ind': 2,
        'R': 549.5
    },
    {
        'ind': 3,
        'R': 525
    },
]

time = []
R = []
with open('in/Rsep-MCC-sht%d.txt' % shotn_table[shotn], 'r') as probe_file:
    for line in probe_file:
        split_line = line.split()
        time.append(float(split_line[0]) * 1000)
        R.append(float(split_line[1]) * 10)


def interpol(t):
    for t_ind in range(len(time) - 1):
        if time[t_ind] <= t < time[t_ind + 1]:
            return R[t_ind] + (R[t_ind + 1] - R[t_ind]) * (t - time[t_ind]) / (time[t_ind + 1] - time[t_ind])
    fuck


res = []
with open('%s%05d/result.json' % (db_path, shotn), 'r') as result_file:
    res = json.load(result_file)

with open('out/%d.csv' % shotn_table[shotn], 'w') as out_file:
    header = 'time, edge, '
    for poly in polys:
        header += 'R-edge, T_e, err, n_e, err, '
    out_file.write(header[:-2] + '\n')
    for event in res:
        if event['processed_bad']:
            continue
        #if event['timestamp'] < time[0]:
        if event['timestamp'] < 160:
            continue
        if event['timestamp'] > time[-1]:
            break
        r_shift = interpol(event['timestamp'])
        line = '%.1f, %.1f, ' % (event['timestamp'], r_shift)
        for poly_req in polys:
            line += '%.1f, ' % (poly_req['R'] - r_shift - 20)
            poly = event['T_e'][poly_req['ind']]
            if poly['processed_bad']:
                line += '--, --, '
                line += '--, --, '
            else:
                line += '%.1f, %.1f, ' % (poly['T'], poly['Terr'])
                line += '%.1f, %.1f, ' % (poly['n'], poly['n_err'])
        out_file.write(line[:-2] + '\n')
print('OK')
