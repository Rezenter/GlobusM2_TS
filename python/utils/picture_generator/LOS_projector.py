import json

shotn: int = 45925
event_ind: int = 60
poly_ind: int = 8

def project_LOS(shotn: int, event_ind: int, poly_ind: int) -> dict:
    with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%d\\result.json' % shotn, 'r') as file:
        ts = json.load(file)

        if 'LOS' not in ts['config']['fibers'][ts['config']['poly'][poly_ind]['fiber']]:
            if ts['config_name'].startswith('2024.08.30'):
                with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\45925\\result.json', 'r') as file2:
                    tmp = json.load(file2)
                    ts['config']['fibers'] = tmp['config']['fibers']

        los = ts['config']['fibers'][ts['config']['poly'][poly_ind]['fiber']]['LOS']
        for point in los:
            point['val'] = ts['events'][event_ind]['T_e'][point['poly_ind']]
        return los

los = project_LOS(shotn, event_ind, poly_ind)
for point in los:
    print(point['L'], point['val']['T'], point['val']['n'])

print('\n\nOK')
