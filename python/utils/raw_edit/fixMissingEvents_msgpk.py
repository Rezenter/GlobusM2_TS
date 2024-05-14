import msgpack
from pathlib import Path
import math

shotn: int = 44298

#DB_PATH: str = 'd:/data/db/'
DB_PATH: str = '\\\\172.16.12.130\\d\\data\\db\\'
PLASMA_FOLDER: str = 'plasma/'
DEBUG_FOLDER: str = 'debug/'
RAW_FOLDER: str = 'raw/'
HEADER_FILE: str = 'header'
FILE_EXT: str = 'json'

shot_folder: Path = Path('%s%s%s%05d/' % (DB_PATH, PLASMA_FOLDER, RAW_FOLDER, shotn))


print('loading raw shot...')
data = []
fixed_data = []

Path(Path('%s%ssafe/%05d/' % (DB_PATH, PLASMA_FOLDER, shotn))).mkdir()
for board_ind in range(8):
    path = Path(shot_folder.joinpath('%d.msgpk' % board_ind))
    with path.open(mode='rb') as file:
        data.append(msgpack.unpackb(file.read()))
    path = Path(Path('%s%ssafe/%05d/%d.msgpk' % (DB_PATH, PLASMA_FOLDER, shotn, board_ind)))
    with path.open(mode='wb') as file:
        msgpack.dump(data[board_ind], file)
    fixed_data.append([data[board_ind][0] for i in range(101)])


for event in range(101):
    for board_ind in range(8):
        ev_ind = math.floor(data[board_ind][event]['t'] / 3.03)
        print(board_ind, ev_ind, data[board_ind][event]['t'])
        if ev_ind < 101:
          fixed_data[board_ind][ev_ind] = data[board_ind][event]
    print('\n')


for event in range(101):
    for board_ind in range(8):
        print(board_ind, event, fixed_data[board_ind][event]['t'])
    print('\n')



for board_ind in range(8):
    path = Path(shot_folder.joinpath('%d.msgpk' % board_ind))
    print(path)
    with path.open(mode='wb') as file:
        msgpack.dump(fixed_data[board_ind], file)


print('OK')
