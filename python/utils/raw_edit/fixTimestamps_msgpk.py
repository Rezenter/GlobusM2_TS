import msgpack
from pathlib import Path
import purge_calculations

is_plasma: bool = True
shotn: int = 44057
#shotn: int = 42516

DB_PATH: str = 'd:/data/db/'
PLASMA_FOLDER: str = 'plasma/'
DEBUG_FOLDER: str = 'debug/'
RAW_FOLDER: str = 'raw/'
HEADER_FILE: str = 'header'
FILE_EXT: str = 'json'
OUT_FOLDER: str = 'local_db/raw/'

if is_plasma:
    shot_folder: Path = Path('%s%s%s%05d/' % (DB_PATH, PLASMA_FOLDER, RAW_FOLDER, shotn))
else:
    shot_folder: Path = Path('%s%s%s%05d/' % (DB_PATH, DEBUG_FOLDER, RAW_FOLDER, shotn))


print('loading raw shot...')
for board_ind in range(8):
    path = Path(shot_folder.joinpath('%d.msgpk' % board_ind))
    with path.open(mode='rb') as file:
        data = msgpack.unpackb(file.read())
        data[0]['t'] = 0
        start: float = data[1]['t'] - 3.03
        for event_ind in range(1, len(data)):
            data[event_ind]['t'] -= start
    with path.open(mode='wb') as file:
        pass
        msgpack.dump(data, file)
    print(' Board %d loaded.' % board_ind)
print('All data is loaded.')
purge_calculations.purge_calc(shotn)

print('OK')
