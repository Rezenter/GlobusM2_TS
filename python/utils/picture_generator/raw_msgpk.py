import msgpack
from pathlib import Path

shotn: int = 41615
board: int = 7
event: int = 55

DB_PATH = 'd:/data/db/plasma/raw'
filename: Path = Path('%s/%05d/%d.msgpk' % (DB_PATH, shotn, board))
with open(filename, 'rb') as file:
    data = msgpack.unpackb(file.read())[event]
    for cell in range(1024):
        line = ''
        for ch in range(16):
            line += '%d ' % data['ch'][ch][cell]
        print(line)

print('OK')