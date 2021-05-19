import json

import integrator
import integration_viewer
import calculator


'''shotn = 40103
events = [38    , 44    , 50    , 56    , 62    , 68]
sync_event = 0  # index of ADC event
#Warning! bad sync
delays = [176.2 , 198.6 , 169.3 , 193.5 , 157.2 , 178.0]  # position in ns of 1047 ch3 peak in poly_ind=9'''

'''shotn = 40105
events = [39    , 45    , 51    , 57    , 63    , 69   , 75]
sync_event = 1  # index of ADC event
delays = [159.5 , 186.9 , 166.2 , 189.9 , 164.7 , 196.8, 172.9]  # position in ns of 1047 ch3 peak in poly_ind=9'''

'''shotn = 40106
events = [38    , 44    , 50    , 56    , 62    , 68]
sync_event = 1  # index of ADC event
delays = [148.9 , 183.1 , 160.7 , 186.5 , 171.1 , 200.3]  # position in ns of 1047 ch3 peak in poly_ind=9'''

'''shotn = 40108
events = [43    , 49    , 55    , 61    , 67]
sync_event = 1  # index of ADC event
delays = [170.0 , 193.2 , 164.9 , 189.9 , 167.5]  # position in ns of 1047 ch3 peak in poly_ind=9'''

'''shotn = 40109
events = [42, 48, 54, 60, 66]
sync_event = 1  # index of ADC event
delays = [181.2, 160.3, 188.5, 169.8, 191.4]  # position in ns of 1047 ch3 peak in poly_ind=9'''

'''shotn = 40079  # g2
shotn = 40080  # g2
shotn = 40081  # g10
shotn = 40082  # g10
shotn = 40088  # g10
shotn = 40090  # g10'''


shotn = 40082
events = [52, 60, 67, 75, 82, 90]
sync_event = 1  # index of ADC event
delays = [94.3, 94.3, 94.3, 94.3, 94.3, 94.3]  # position in ns of 1047 ch3 peak in poly_ind=9

polys = [1, 6]
channels = [0, 2, 3, 4]

is_plasma = True
config_name = '2021.05.12_g10'

LOCAL_DB_PATH = 'local_db/'
GLOBAL_DB_PATH = 'd:/data/db/'

raw_processor = integrator.Integrator(LOCAL_DB_PATH, shotn, is_plasma, config_name, GLOBAL_DB_PATH)
raw_processor.process_shot(events, delays, sync_event)

print('\nintegrated.\n')

fine_processor = calculator.Processor(LOCAL_DB_PATH, shotn, is_plasma, '2021.02.01', '2021.02.03',
                                      GLOBAL_DB_PATH, '2021.05.18_1047')
if fine_processor.get_error() is not None:
    fine_processor.load()
resp = fine_processor.get_data()

print('\ncalculated.\n')

for poly_ind in polys:
    #integration_viewer.draw(shotn, events, poly_ind)
    with open('%s/result/%05d/%05d.json' % (LOCAL_DB_PATH, shotn, shotn), 'r') as res_file:
        result = json.load(res_file)
    with open('local_db/csv/%05d_poly#%d.csv' % (shotn, poly_ind), 'w') as file:
        file.write('shotn, time_47, time_64, ch1_47, err, ch3_47, err, ch4_47, err, ch5_47, err, ch1_64, err, ch3_64, err, ch4_64, err, ch5_64, err, T_64, err, n_64, err, T_47, err, n_47, err, delay\n')
        file.write('#, ms, ms, ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., eV, eV, parr, parr, eV, eV, parr, parr, ns\n')
        for event_ind in range(len(events)):
            line = '%05d, %.1f, %.1f, ' % (shotn, raw_processor.processed[event_ind]['timestamp'], raw_processor.processed[event_ind]['timestamp'])
            for ch in channels:
                line += '%.1f, %.1f, ' % (raw_processor.processed[event_ind]['1047'][poly_ind][ch]['ph_el'],
                                          raw_processor.processed[event_ind]['1047'][poly_ind][ch]['err'])
            for ch in channels:
                line += '%.1f, %.1f, ' % (raw_processor.processed[event_ind]['1064'][poly_ind][ch]['ph_el'],
                                          raw_processor.processed[event_ind]['1064'][poly_ind][ch]['err'])
            res_ev = result['1064'][event_ind]
            if 'T' in res_ev['T_e'][poly_ind]:
                line += '%.1f, %.1f, %.2e, %.2e, ' % (res_ev['T_e'][poly_ind]['T'], res_ev['T_e'][poly_ind]['Terr'], res_ev['T_e'][poly_ind]['n'], res_ev['T_e'][poly_ind]['n_err'])
            else:
                line += '--, --, --, --, '
            res_ev = result['1047'][event_ind]
            if 'T' in res_ev['T_e'][poly_ind]:
                line += '%.1f, %.1f, %.2e, %.2e, ' % (
                res_ev['T_e'][poly_ind]['T'], res_ev['T_e'][poly_ind]['Terr'], res_ev['T_e'][poly_ind]['n'],
                res_ev['T_e'][poly_ind]['n_err'])
            else:
                line += '--, --, --, --, '
            line += '%.1f\n' % delays[event_ind]
            file.write(line)
print('OK')
