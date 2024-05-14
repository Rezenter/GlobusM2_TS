import msgpack
from pathlib import Path
import math

shotn: int = 44057

DB_PATH: str = 'd:/data/db/'
PLASMA_FOLDER: str = 'plasma/'
DEBUG_FOLDER: str = 'debug/'
RAW_FOLDER: str = 'raw/'
HEADER_FILE: str = 'header'
FILE_EXT: str = 'json'
OUT_FOLDER: str = 'local_db/raw/'


shot_folder: Path = Path('%s%s%s%05d/' % (DB_PATH, PLASMA_FOLDER, RAW_FOLDER, shotn))

start_ind: int = 2

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
    fixed_data.append([data[board_ind][i] for i in range(start_ind, 101)])



for board_ind in range(8):
    path = Path(shot_folder.joinpath('%d.msgpk' % board_ind))
    with path.open(mode='wb') as file:
        msgpack.dump(fixed_data[board_ind], file)


print('OK')
