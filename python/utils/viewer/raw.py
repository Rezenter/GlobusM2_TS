import sys
import os
import matplotlib.pyplot as plt
import gc

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

is_plasma = False
shotn = 383
config = '2020.12.08_raman'

integrator = rawToSignals.Integrator(DB_PATH, shotn, is_plasma, config)
if not integrator.loaded:
    integrator.load_raw()


def plot(poly_ind, event_ind):
    print('Plotting poly %d' % poly_ind)
    fig = plt.figure()
    tmp = None
    for ch_ind in range(len(integrator.config['poly'][poly_ind]['channels'])):
        sp_ch = integrator.config['poly'][poly_ind]['channels'][ch_ind]
        board_ind = sp_ch['adc']
        if 'captured_bad' in integrator.result[board_ind][event_ind] and integrator.result[board_ind][event_ind][
            'captured_bad']:
            continue
        # if 'processed_bad' in laser['boards'][board_ind] and laser['boards'][board_ind]['processed_bad']:
        #    continue
        if 'skip' in sp_ch and sp_ch['skip']:
            continue
        adc_gr, adc_ch = integrator.ch_to_gr(sp_ch['ch'])
        signal = integrator.result[board_ind][event_ind][adc_gr]['data'][adc_ch]
        start = integrator.processed[event_ind]['laser']['boards'][board_ind]['sync_ind']
        tmp = plt.plot([(cell_ind - start) * integrator.time_step for cell_ind in range(len(signal))],
                       [y - integrator.processed[event_ind]['poly']['%d' % poly_ind]['ch'][ch_ind]['zero_lvl'] for y in
                        signal],
                       label='ch %d' % (ch_ind + 1))
        plt.gca().axvspan(
            (integrator.processed[event_ind]['poly']['%d' % poly_ind]['ch'][ch_ind][
                 'from'] - start) * integrator.time_step,
            (integrator.processed[event_ind]['poly']['%d' % poly_ind]['ch'][ch_ind][
                 'to'] - start) * integrator.time_step,
            alpha=0.3, color=tmp[-1].get_color())
        del signal
    plt.ylabel('signal, mV')
    plt.xlabel('timeline, ns')
    plt.title('Poly %d, event %d' % (poly_ind, event_ind))
    plt.xlim(40, 100)
    plt.ylim(-50, 2350)

    plt.gca().legend()
    plt.grid(color='k', linestyle='-', linewidth=1)
    filename = 'figs/ev%d_p%d.png' % (event_ind, poly_ind)
    plt.savefig(filename, dpi=600)
    plt.show()
    plt.clf()
    plt.close(fig)
    del tmp
    gc.collect()

print('Viewer ok')
