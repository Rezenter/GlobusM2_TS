import msgpack
from pathlib import Path

shotn: int = 45511
board: int = 2
event: int = 60

DB_PATH = '\\\\172.16.12.130\\d/data/db/plasma/raw'
filename: Path = Path('%s/%05d/%d.msgpk' % (DB_PATH, shotn, board))
with open(filename, 'rb') as file:
    r = msgpack.unpackb(file.read())
    data = r[event]
    for cell in range(1024):
        line = ''
        for ch in range(16):
            line += '%d, ' % data['ch'][ch][cell]
        print(line[:-2])

print('OK')