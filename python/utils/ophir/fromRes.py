import json
import statistics

shotn = 521
poly_count = 11

with open('d:/data/db/debug/signal/%05d.json' % shotn, 'r') as data_fp:
    data = json.load(data_fp)
if data is None:
    fuck

res = [{
    'mean': 0,
    'std': 0,
    'max': -1e99,
    'min': 1e99,
    'vals': []
} for poly in range(poly_count)]

for event in data:
    for poly_ind in range(poly_count):
        val = event['poly'][poly_ind]['ch'][0]['ph_el']
        res[poly_ind]['vals'].append(val)
        res[poly_ind]['max'] = max(val, res[poly_ind]['max'])
        res[poly_ind]['min'] = max(val, res[poly_ind]['min'])

count = 1
for poly in res:
    poly['mean'] = statistics.mean(poly['vals'])
    poly['std'] = statistics.stdev(poly['vals'])
    print('poly %d: stray = %d ph.el., std = %.2e\n' % (count, poly['mean'], poly['std']))
    count += 1