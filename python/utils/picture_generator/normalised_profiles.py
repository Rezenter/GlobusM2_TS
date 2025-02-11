import json
from pathlib import Path
import statistics

'''shots = [
44168,
44170,
44171,
44172,
44173,
44174,
44181,
44183,
44184,
44185,
44188,
44194,
44198,
44199,
44207,
44347,
44348,
44350,
44351,
44352,
44355
]'''

#MAPE
#P NBI range
#desync elms
#eqdsk?

saw_delay = 1e-4 # s

index = None
path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.json')
with open(path, 'r') as file:
    index = json.load(file)

res = []

normalised = []

#R -21 to 2.5, 40 bins
#V/<V> min-max, 40 bins


shot_out = 0
with open('out/normalised.csv', 'w') as out_file:
    out_file.write('shotn, time, R-R_lcfs, T_e/<Te>, n_e/<ne>, I_p, B_T, Volume, W_e, l42, <n>l, elong, before sawtooth #, Upl*Ipl, NBI1, NBI2, <Te>, <ne>, R\n')
    #for shotn in shots:
    for shotn in range(41500, 46000):

        if shotn - shot_out > 100:
            shot_out = shotn
            print(shotn)
        path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\cfm_res.json' % shotn)
        ts = None
        if not path.exists():
            continue
        with open(path, 'r') as file:
            tmp = json.load(file)
            if 'data' not in tmp:
                continue
            ts = tmp['data']
        path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\result.json' % shotn)
        if not path.exists():
            continue
        res = None
        if 'T_flattop_stop' not in index['%d' % shotn] or 'T_flattop_start' not in index['%d' % shotn]:
            continue
        if index['%d' % shotn]['T_flattop_stop'] - index['%d' % shotn]['T_flattop_start'] < 0.01:
            continue
        with open(path, 'r') as file:
            res = json.load(file)
        entry = []
        for ev in ts:
            if 'T_e' not in res['events'][ev['event_index']]:
                continue
            res_ev = res['events'][ev['event_index']]['T_e']
            if 'TS' not in index['%d' % shotn]:
                continue
            if ev['event_index'] > len(index['%d' % shotn]['TS']['time']) - 1:
                continue
            if index['%d' % shotn]['T_flattop_stop'] < index['%d' % shotn]['TS']['time'][ev['event_index'] - 1]:
                continue
            if index['%d' % shotn]['T_flattop_start'] > index['%d' % shotn]['TS']['time'][ev['event_index'] - 1]:
                continue
            if 0.140 >= index['%d' % shotn]['TS']['time'][ev['event_index'] - 1]:
                continue
            if 'data' not in ev:
                continue
            if 'surfaces' not in ev['data']:
                continue
            if len(ev['data']['surfaces']) < 2:
                continue
            if ev['data']['surfaces'][0]['r_max'] >= 60.8:
                continue
            skip: bool = False
            for saw in index['%d' % shotn]['SXR']['time']:
                if index['%d' % shotn]['TS']['time'][ev['event_index'] - 1] - saw_delay <= saw['time'] <= index['%d' % shotn]['TS']['time'][ev['event_index'] - 1] + saw_delay:
                    #print('too close', shotn, saw['time'])
                    skip = True
                    break
            if skip:
                continue

            before_saw = 999
            for i in range(len(index['%d' % shotn]['SXR']['time'])):
                if index['%d' % shotn]['TS']['time'][ev['event_index'] - 1] + saw_delay <= index['%d' % shotn]['SXR']['time'][i]['time']:
                    before_saw = i + 1
                    break
            else:
                before_saw = i + 1


            tmp = []
            for poly_ind in range(len(res_ev)):
                if 'T' not in res_ev[poly_ind]:
                    continue
                if 'hidden' in res_ev[poly_ind] and res_ev[poly_ind]['hidden']:
                    continue
                if not 3 <= res_ev[poly_ind]['T'] <= 1900:
                    continue
                #if res['config']['poly'][poly_ind]['R']*0.1 - ev['data']['surfaces'][0]['r_max'] < -8.45:
                #    continue
                if res_ev[poly_ind]['Terr']/res_ev[poly_ind]['T'] >= 0.5:
                    continue
                if res_ev[poly_ind]['chi2'] >= 10:
                    continue
                nbi1 = 0
                nbi2 = 0
                if 'I_max' in index['%d' % shotn]['NBI1'] and 'U' in index['%d' % shotn]['NBI1']:
                    nbi1 = max(index['%d' % shotn]['NBI1']['I_max'] * index['%d' % shotn]['NBI1']['U'] * 1e-3, 0)

                if 'I_max' in index['%d' % shotn]['NBI2'] and 'U_max' in index['%d' % shotn]['NBI2']:
                    nbi2 = max(index['%d' % shotn]['NBI2']['I_max'] * index['%d' % shotn]['NBI2']['U_max'], 0)


                entry = {
                    'shotn': shotn,
                    'time': index['%d' % shotn]['TS']['time'][ev['event_index'] - 1]*1000,
                    'R-R_lcfs': res['config']['poly'][poly_ind]['R']*0.1 - ev['data']['surfaces'][0]['r_max'],
                    'T_e/<Te>': res_ev[poly_ind]['T'] / ev['data']['t_vol'],
                    'n_e/<ne>': res_ev[poly_ind]['n'] / ev['data']['n_vol'],
                    'I_p': index['%d' % shotn]['Ip'],
                    'B_T': index['%d' % shotn]['Bt'],
                    'Volume': ev['data']['vol'],
                    'W_e': ev['data']['vol_w']*1e-3,
                    'l42': ev['data']['nl_profile'][0]['z'] - ev['data']['nl_profile'][-1]['z'],
                    '<n>l': ev['data']['nl']*1e-19,
                    'elong': (ev['data']['surfaces'][0]['z_max']-ev['data']['surfaces'][0]['z_min'])/(ev['data']['surfaces'][0]['r_max'] - ev['data']['surfaces'][0]['r_min']),
                    'before sawtooth #': before_saw,
                    'Upl*Ipl': max(index['%d' % shotn]['TS']['Upl'][ev['event_index'] - 1] * index['%d' % shotn]['Ip'], 0),
                    'NBI1': nbi1,
                    'NBI2': nbi2,
                    '<Te>': ev['data']['t_vol'],
                    '<ne>': ev['data']['n_vol']*1e-19,
                    'R': res['config']['poly'][poly_ind]['R'] * 0.1
                }
                tmp.append(entry)

            if len(tmp) >= 6:
                normalised.extend(tmp)
                for e in tmp:
                    out_file.write('%d, %.2f, %.3f, %.3e, %.3e, %d, %.3f, %.3f, %.3f, %.2f, %.3f, %.3f, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.1f\n'
                        % (e['shotn'],
                           e['time'],
                           e['R-R_lcfs'],
                           e['T_e/<Te>'],
                           e['n_e/<ne>'],
                           e['I_p'],
                           e['B_T'],
                           e['Volume'],
                           e['W_e'],
                           e['l42'],
                           e['<n>l'],
                           e['elong'],
                           e['before sawtooth #'],
                           e['Upl*Ipl'],
                           e['NBI1'],
                           e['NBI2'],
                           e['<Te>'],
                           e['<ne>'],
                           e['R']
                           )
                    )

with open('out/normalised.json', 'w') as out_file:
    json.dump(normalised, out_file, indent=2)

print('Code OK')
