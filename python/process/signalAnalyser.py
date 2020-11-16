import ijson
import math

extension = '.json'
config_path = '../configs/'

shotn = 294
file_path = 'd:/data/signals/%05d.json' % shotn

events = []
with open(file_path, 'rb') as processed_file:
    event_ind = 0
    for event in ijson.items(processed_file, 'data.item', use_float=True):
        events.append(event)

for poly_ind in range(10):
    with open('out/p%02d.csv' % poly_ind, 'w') as out_file:
        out_file.write(
            'event, ch1, err, ch2, err, ch3, err, ch4, err, ch5, err\n'
            '1, ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el., ph.el.\n'
        )
        for event_ind in range(380, 419):
            event = events[event_ind]
            if not event['processed_bad']:
                line = '%d, ' % event_ind
                for ch_ind in range(5):
                    if event['poly']['%d' % poly_ind]['ch'][ch_ind]['processed_bad']:
                        line += ', , '
                    else:
                        signal = event['poly']['%d' % poly_ind]['ch'][ch_ind]['ph_el']
                        std2 = math.pow(event['poly']['%d' % poly_ind]['ch'][ch_ind]['pre_std'], 2)
                        err2 = std2*6715*0.0625 - 1.14e4*0.0625
                        err = math.sqrt(math.fabs(err2) + math.fabs(signal) * 4)
                        line += '%.2f, %.2f, ' % (signal, err)

            out_file.write('%s\n' % line[:-2])
print('ok')
