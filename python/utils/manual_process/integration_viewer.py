import json
import matplotlib.pyplot as plt


channels = [0, 2, 3]
colors = ['k', 'r', 'b', 'g', 'm', 'c', 'y']

def draw(shotn, events, poly):
    with open('local_db/export/%05d.json' % shotn, 'r') as file:
        data = json.load(file)

    for event_ind in events:
        print('event: ', event_ind, data[event_ind]['timestamp'])
        print('poly: ', poly)
        if '1047' in data[event_ind]['ts']:
            entry = data[event_ind]['ts']['1047'][poly]
            for ch in channels:
                plt.plot(range(1024), [v - entry[ch]['zero_lvl'] for v in entry[ch]['raw']], color=colors[ch])
                plt.fill_between([entry[ch]['from'], entry[ch]['to']], entry[ch]['int'] * 0.1, color=colors[ch], alpha=0.3)
            plt.legend(['ch %d' % (ch + 1) for ch in channels])
            plt.title('%05d, event %.d = %.1f, poly %d' % (shotn, event_ind, data[event_ind]['timestamp'], poly))
            plt.show()
            plt.clf()
            print('_____\n')

