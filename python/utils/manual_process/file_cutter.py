import ijson
import json
import os

is_plasma = True
shotn = 40105
start_ind = 648
stop_ind = 723

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


dest_folder = '%s%05d/' % (OUT_FOLDER, shotn)
if os.path.isdir(dest_folder):
    print('Output folder exists')
    exit()
os.mkdir(dest_folder)

data = load_raw()
with open('%s%s.%s' % (dest_folder, HEADER_FILE, FILE_EXT), 'w') as file:
    json.dump(header, file)
print('dumping...')
for board_ind in range(len(data)):
    with open('%s%d.%s' % (dest_folder, board_ind, FILE_EXT), 'w') as file:
        json.dump(data[board_ind][start_ind: stop_ind], file)
    print(' Board %d dumped.' % board_ind)
print('OK')
