import json
import sys
sys.path.append('../python')
from python.utils.reconstruction import CurrentCoils
from python.utils.reconstruction import stored_energy
import math


req_file: str = 'Ip300_Bt07_250-400'
use_boundaty_shotn: int = 44273
use_boundaty_time: float = 167.3


db: str = ('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\')
theta_step = 0.2 * math.pi / 180  # rad
ra_step = 0.01  # cm
ra_center = 0.001  # 1

res = {
    'in_file': req_file,
    'selected boundary': {
        'shotn': use_boundaty_shotn,
        'time': use_boundaty_time
    },
    'request': [],
    'averaged': []
}

with open('in/%s.csv' % req_file, 'r') as file:
    header = file.readline()[:-1].split(',')
    #shotn_col = header.index('shotn')
    shotn_col = header.index('shot#')
    time_col = header.index('time')
    #file.readline() # units
    for line in file:
        spl = line.split(',')
        #res['request'].append((int(float(spl[shotn_col])), float(spl[time_col])*1e3))
        res['request'].append({
            'shotn': int(spl[shotn_col]),
            'time': float(spl[time_col])*1e3
        })

r = []
te_out = []
ne_out = []
te_dict = {}
ne_dict = {}
cfm_data = []

for req in res['request']:
    req['R'] = []
    req['Te'] = []
    req['Te err'] = []
    req['ne'] = []
    req['ne err'] = []


    with open('%s%05d\\%05d_T(R).csv' % (db, req['shotn'], req['shotn'])) as file:
        header = file.readline().split(', ')
        time_col = header.index('%.1f' % req['time'])
        te = [(req['shotn'], req['time'])]
        r_tmp = []

        file.readline()
        for line in file:
            spl = line.split(', ')
            r_tmp.append(float(spl[0]))
            req['R'].append(float(spl[0]))
            te.append((spl[time_col].strip(), spl[time_col + 1].strip()))
            req['Te'].append(spl[time_col].strip())
            req['Te err'].append(spl[time_col + 1].strip())

        for i in range(len(r_tmp)):
            if r_tmp[i] not in te_dict:
                te_dict[r_tmp[i]] = []
            if te[i+1][0] != '--':
                te_dict[r_tmp[i]].append(te[i+1])
        if len(r) == 0:
            r = r_tmp
        else:
            for i in range(len(r)):
                if len(r_tmp) == i or r[i] != r_tmp[i]:
                    r_tmp.insert(i, r[i])
                    te.insert(i, ('--', '--'))
                    #fuck
        te_out.append(te)

    with open('%s%05d\\%05d_n(R).csv' % (db, req['shotn'], req['shotn'])) as file:
        header = file.readline().split(', ')
        time_col = header.index('%.1f' % req['time'])
        ne = [(req['shotn'], req['time'])]
        r_tmp = []

        file.readline()
        for line in file:
            spl = line.split(', ')
            r_tmp.append(float(spl[0]))
            ne.append((spl[time_col].strip(), spl[time_col + 1].strip()))
            req['ne'].append(spl[time_col].strip())
            req['ne err'].append(spl[time_col + 1].strip())
        for i in range(len(r_tmp)):
            if r_tmp[i] not in ne_dict:
                ne_dict[r_tmp[i]] = []
            if ne[i+1][0] != '--':
                ne_dict[r_tmp[i]].append(ne[i+1])
        if len(r) == 0:
            r = r_tmp
        else:
            for i in range(len(r)):
                if len(r_tmp) == i or r[i] != r_tmp[i]:
                    r_tmp.insert(i, r[i])
                    ne.insert(i, ('--', '--'))
        ne_out.append(ne)


    cfm = CurrentCoils.CCM(shotn=req['shotn'])
    time = req['time'] * 1e-3
    t_ind: int = 0
    for t_ind in range(len(cfm.timestamps) - 1):
        if cfm.timestamps[t_ind] <= time < cfm.timestamps[t_ind + 1]:
            if (time - cfm.timestamps[t_ind]) >= (cfm.timestamps[t_ind + 1] - time):
                t_ind += 1
            break
    if len(cfm.data['boundary']['rbdy']['variable'][t_ind]) == 0:
        fuck
    cfm.data['boundary']['rbdy']['variable'][t_ind], cfm.data['boundary']['zbdy']['variable'][t_ind] = \
        cfm.clockwise(cfm.data['boundary']['rbdy']['variable'][t_ind],
                      cfm.data['boundary']['zbdy']['variable'][t_ind],
                      t_ind)

    req['LCFS'] = {
        'r': cfm.data['boundary']['rbdy']['variable'][t_ind],
        'z': cfm.data['boundary']['zbdy']['variable'][t_ind],
        'shotn': req['shotn'],
        'time': req['time']
    }
    cfm_data.append(req['LCFS'])



ts_res = {
    'events': [
        {},
        {
            'timestamp': use_boundaty_time,
            'T_e': [],
            'error': None
        }
    ],
    'config':{
        'poly':[]
    }
}

i = 0
for r in te_dict:
    r_te = te_dict[r]
    r_ne = ne_dict[r]


    te_top: float = 0
    te_sum: float = 0
    for pair in r_te:
        weight = (float(pair[0]) / float(pair[1])) ** 2
        te_top += float(pair[0]) * weight
        te_sum += weight

    ne_top: float = 0
    ne_sum: float = 0
    for pair in r_ne:
        weight = (float(pair[0]) / float(pair[1])) ** 2
        ne_top += float(pair[0]) * weight
        ne_sum += weight

    ts_res['config']['poly'].append({
        'ind': len(ts_res['config']['poly']),
        'R': r
    })


    res['averaged'].append({
        'ind': i,
        'R': r,
        'T': te_top / te_sum,
        'Terr': (1 / te_sum) ** 0.5,
        'n': ne_top / ne_sum,
        'n_err': (1 / ne_sum) ** 0.5,
        'error': None
    })
    i += 1
ts_res['events'][1]['T_e'] = res['averaged']


stored_calc = stored_energy.StoredCalculator(shotn=use_boundaty_shotn, ts_data=ts_res, shift=999)
if stored_calc.error is not None:
    fuck
stored = stored_calc.calc_dynamics(t_from=use_boundaty_time-1, t_to=use_boundaty_time+1)
if stored_calc.error is not None:
    fuck
res['integrated'] = stored['data'][0]['data']


with open('out/%s.json' % req_file, 'w') as file:
    json.dump(res, file, indent=2)

print('JSON created OK')


te_lines = []
ne_lines = []
bound_lines = []

line = ''
rz_line = ''
max_len = 0
max_rz_len = 0
for req in res['request']:
    line += 'R, %d_%.1f, err, ' % (req['shotn'], req['time'])
    rz_line += 'R, %d_%.1f, ' % (req['shotn'], req['time'])
    max_len = max(len(req['R']), max_len)
    max_rz_len = max(len(req['LCFS']['r']), max_rz_len)

line += 'R, ave, err\n'

te_lines.append(line)
ne_lines.append(line)
bound_lines.append(rz_line[: -2] + '\n')

for i in range(max_len):
    t_line = ''
    n_line = ''

    for req in res['request']:
        if i < len(req['R']):
            t_line += '%.2f, %s, %s, ' % (req['R'][i], req['Te'][i], req['Te err'][i])
            n_line += '%.2f, %s, %s, ' % (req['R'][i], req['ne'][i], req['ne err'][i])
        else:
            t_line += '--, --, --, '
            n_line += '--, --, --, '
    t_line += '%.2f, %s, %s\n' % (res['averaged'][i]['R'], res['averaged'][i]['T'], res['averaged'][i]['Terr'])
    n_line += '%.2f, %s, %s\n' % (res['averaged'][i]['R'], res['averaged'][i]['n'], res['averaged'][i]['n_err'])

    te_lines.append(t_line)
    ne_lines.append(n_line)


with open('out/%s_Te.csv' % req_file, 'w') as file:
   for line in te_lines:
       file.write(line)

with open('out/%s_ne.csv' % req_file, 'w') as file:
   for line in ne_lines:
       file.write(line)

for i in range(max_rz_len):
    rz_line = ''

    for req in res['request']:
        if i < len(req['LCFS']['r']):
            rz_line += '%.2f, %s, ' % (req['LCFS']['r'][i], req['LCFS']['z'][i])
        else:
            rz_line += '--, --, '

    bound_lines.append(rz_line[: -2] + '\n')

with open('out/%s_LCFS.csv' % req_file, 'w') as file:
   for line in bound_lines:
       file.write(line)

print('code OK')
