import json
import statistics

shotn = 529
poly_count = 11
ch_count = 2

with open('d:/data/db/debug/signal/%05d.json' % shotn, 'r') as data_fp:
    data = json.load(data_fp)
if data is None:
    fuck

res = [[{
    'mean': 0,
    'std': 0,
    'max': -1e99,
    'min': 1e99,
    'vals': []
}, {
    'mean': 0,
    'std': 0,
    'max': -1e99,
    'min': 1e99,
    'vals': []
}] for poly in range(poly_count)]

for event in data['data']:
    for poly_ind in range(poly_count):
        for ch in range(ch_count):
            if event['poly']['%d' % poly_ind]['ch'][ch]['error']:
                continue
            val = event['poly']['%d' % poly_ind]['ch'][ch]['ph_el']
            res[poly_ind][ch]['vals'].append(val)
            res[poly_ind][ch]['max'] = max(val, res[poly_ind][ch]['max'])
            res[poly_ind][ch]['min'] = min(val, res[poly_ind][ch]['min'])

count = 1
for poly in res:
    line = '%d ' % count
    for ch in range(ch_count):
        if len(poly[ch]['vals']) > 0:
            poly[ch]['mean'] = statistics.mean(poly[ch]['vals'])
            poly[ch]['std'] = statistics.stdev(poly[ch]['vals'])
        else:
            poly[ch]['mean'] = 0
            poly[ch]['std'] = 0
        if count <= 2 and False:
            poly[ch]['mean'] *= 2
            poly[ch]['std'] *= 2
            poly[ch]['min'] *= 2
            poly[ch]['max'] *= 2
        line += '%d %d ' % (poly[ch]['mean'], poly[ch]['std'])

    print(line)
    count += 1