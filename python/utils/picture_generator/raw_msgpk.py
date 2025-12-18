import msgpack
from pathlib import Path

shotn: int = 46339
board: int = 0
event: int = 60

DB_PATH = 'd:/data/db/plasma/raw'
#DB_PATH = 'd:/data/db/debug/raw'
filename: Path = Path('%s/%05d/%d.msgpk' % (DB_PATH, shotn, board))

with open(filename, 'rb') as file:
    r = msgpack.unpackb(file.read())
    #print(len(r))
    #for e in r:
    #    print(e['t'])

    data = r[event]
    for cell in range(1024):
        line = ''
        for ch in range(16):
            line += '%d, ' % data['ch'][ch][cell]
        print(line[:-2])

print('OK')