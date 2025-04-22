import sys
import os
import matplotlib.pyplot as plt
import gc
import json

PACKAGE_PARENT = '../..'  # "python" directory
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from process import rawToSignals

DB_PATH = 'd:/data/db/'
PLASMA_SHOTS = 'plasma/'
DEBUG_SHOTS = 'debug/'
RAW_FOLDER = 'raw/'
HEADER_FILE = 'header'
FILE_EXT = 'json'

is_plasma = True
shotn = 41505
config = '2021.11.02_g2-10'

integrator = rawToSignals.Integrator(DB_PATH, shotn, is_plasma, config)
print(integrator.error)
if not integrator.loaded:
    integrator.load_raw()


def plot(poly_ind, event_ind, xlim, ylim):
    print('Plotting poly %d' % poly_ind)
    fig = plt.figure()
    tmp = None
    dumping = []
    for ch_ind in range(len(integrator.config['poly'][poly_ind]['channels'])):
        sp_ch = integrator.config['poly'][poly_ind]['channels'][ch_ind]
        board_ind = sp_ch['adc']
        if 'captured_bad' in integrator.cfm_data[board_ind][event_ind] and \
                integrator.cfm_data[board_ind][event_ind]['captured_bad']:
            continue
        # if 'processed_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['processed_bad']:
        #    continue
        if 'skip' in sp_ch and sp_ch['skip']:
            continue

        #adc_gr, adc_ch = integrator.ch_to_gr(sp_ch['ch'])
        #signal = integrator.data[board_ind][event_ind][adc_gr]['data'][adc_ch]

        signal = integrator.cfm_data[board_ind][event_ind]['ch'][sp_ch['ch']]

        start = integrator.processed[event_ind]['laser']['boards'][board_ind]['sync_ind']
        x = [(cell_ind - start) * integrator.time_step for cell_ind in range(len(signal))]
        y = [y - integrator.processed[event_ind]['poly']['%d' % poly_ind]['ch'][ch_ind]['zero_lvl'] for y in signal]
        tmp = plt.plot(x, y, label='ch %d' % (ch_ind + 1))
        dumping.append({
            'x': x,
            'y': y
        })
        plt.gca().axvspan(
            (integrator.processed[event_ind]['poly']['%d' % poly_ind]['ch'][ch_ind]['from'] - start) *
            integrator.time_step,
            (integrator.processed[event_ind]['poly']['%d' % poly_ind]['ch'][ch_ind]['to'] - start) *
            integrator.time_step, alpha=0.3, color=tmp[-1].get_color())
        del signal

    with open('dump.csv', 'w') as dump:
        for cell in range(1024):
            line = ''
            for ch in dumping:
                line += '%.2f, %.2f, ' % (ch['x'][cell], ch['y'][cell])
            dump.write(line[:-2] + '\n')
    print('dumped')
    plt.ylabel('signal, mV')
    plt.xlabel('timeline, ns')
    plt.title('Poly %d, event %d' % (poly_ind, event_ind))
    plt.xlim(xlim)
    plt.ylim(ylim)

    plt.gca().legend()
    plt.grid(color='k', linestyle='-', linewidth=1)
    filename = 'figs/ev%d_p%d.png' % (event_ind, poly_ind)
    plt.savefig(filename, dpi=600)
    plt.show()
    plt.clf()
    plt.close(fig)
    del tmp
    gc.collect()


def csv(poly_ind, event_ind):
    print('Plotting poly %d' % poly_ind)
    fig = plt.figure()

    dumping = []

    sp_ch = integrator.config['poly'][poly_ind]['channels'][0]
    board_ind = sp_ch['adc']
    laser = integrator.cfm_data[board_ind][event_ind]['ch'][integrator.config['adc']['sync'][board_ind]['ch']]
    dumping.append(laser)

    for ch_ind in range(len(integrator.config['poly'][poly_ind]['channels'])):
        sp_ch = integrator.config['poly'][poly_ind]['channels'][ch_ind]
        board_ind = sp_ch['adc']
        if 'captured_bad' in integrator.cfm_data[board_ind][event_ind] and \
                integrator.cfm_data[board_ind][event_ind]['captured_bad']:
            continue
        # if 'processed_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['processed_bad']:
        #    continue
        if 'skip' in sp_ch and sp_ch['skip']:
            continue

        # adc_gr, adc_ch = integrator.ch_to_gr(sp_ch['ch'])
        # signal = integrator.data[board_ind][event_ind][adc_gr]['data'][adc_ch]
        signal = integrator.cfm_data[board_ind][event_ind]['ch'][sp_ch['ch']]
        dumping.append(signal)
        del signal

    with open('%d.csv' % event_ind, 'w') as dump:
        for ch in dumping:
            line = ''
            for cell in range(1024):
                line += '%.2f, ' % ch[cell]
            dump.write(line[:-2] + '\n')
    print('dumped')
    gc.collect()

print('Viewer ok')
