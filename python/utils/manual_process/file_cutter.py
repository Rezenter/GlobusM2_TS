import ijson
import json
import os
import shutil

is_plasma = True
shotn = 40215
start_ind = 173


stop_ind = start_ind + 100

DB_PATH = 'd:/data/db/'
PLASMA_FOLDER = 'plasma/'
DEBUG_FOLDER = 'debug/'
RAW_FOLDER = 'raw/'
HEADER_FILE = 'header'
FILE_EXT = 'json'
OUT_FOLDER = 'local_db/raw/'

if is_plasma:
    shot_folder = '%s%s%s%05d/' % (DB_PATH, PLASMA_FOLDER, RAW_FOLDER, shotn)
else:
    shot_folder = '%s%s%s%05d/' % (DB_PATH, DEBUG_FOLDER, RAW_FOLDER, shotn)

with open('%s%s.%s' % (shot_folder, HEADER_FILE, FILE_EXT), 'r') as file:
    header = json.load(file)


def load_raw():
    data = []
    print('loading raw shot...')
    for board_ind in range(len(header['boards'])):
        with open('%s%d.%s' % (shot_folder, board_ind, FILE_EXT), 'rb') as board_file:
            data.append([])
            for event in ijson.items(board_file, 'item', use_float=True):
                data[board_ind].append(event)
        print(' Board %d loaded.' % board_ind)
    print('All data is loaded.')
    if not check_raw_integrity(data):
        fuck
    return data


def check_raw_integrity(data):
    laser_count = len(data[0])
    for board_ind in range(1, len(data)):
        if len(data[board_ind]) != laser_count:
            print('Boards recorded different number of events! %d vs %d' %
                  (len(data[board_ind]), laser_count))
            return False
            print('\n WARNING! check failed but commented for debug!\n')
            laser_count = min(laser_count, len(data[board_ind]))

    print('Total event count = %d.' % laser_count)
    return True


data = load_raw()

if os.path.isdir('%s' % shot_folder):
    shutil.rmtree('%s' % shot_folder)
    os.mkdir('%s' % shot_folder)
    print('Removed original raw')
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


with open('%s%s.%s' % (shot_folder, HEADER_FILE, FILE_EXT), 'w') as file:
    json.dump(header, file)
print('dumping %d events...' % (stop_ind - start_ind + 1))
for board_ind in range(len(data)):
    with open('%s%d.%s' % (shot_folder, board_ind, FILE_EXT), 'w') as file:
        json.dump(data[board_ind][start_ind: stop_ind + 1], file)
    print(' Board %d dumped.' % board_ind)

print('OK')
