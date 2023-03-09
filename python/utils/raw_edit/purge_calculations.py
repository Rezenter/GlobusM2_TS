import os
import shutil

is_plasma = True

DB_PATH = 'd:/data/db/'
PLASMA_FOLDER = 'plasma/'
DEBUG_FOLDER = 'debug/'
RES_FOLDER = 'result/'
SIG_FOLDER = 'signal/'
FILE_EXT = 'json'


def purge_calc(shotn: int):
    print('Purge %d' % shotn)
    if is_plasma:
        prefix = '%s%s' % (DB_PATH, PLASMA_FOLDER)
    else:
        prefix = '%s%s' % (DB_PATH, DEBUG_FOLDER)
    signal_file = prefix + 'signal/%05d.json' % shotn
    if os.path.isfile(signal_file):
        os.remove(signal_file)
        print('Removed signal file')
    result_folder = prefix + 'result/%05d' % shotn
    if os.path.isdir(result_folder):
        shutil.rmtree(result_folder)
        print('Removed result folder')


purge_calc(42123)

print('OK')
