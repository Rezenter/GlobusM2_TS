import msgpack
from pathlib import Path

dir_new: Path = Path('d:\\data\\db\\plasma\\raw\\')
dir_old: Path = Path('\\\\192.168.10.41\\d\\data\\db\\plasma\\ophir\\')

start: int = 45714
stop: int = 45717

for shot in range(start, stop):
    if  shot > 46155:
        path = dir_new.joinpath('%05d\\ophir.msgpk' % (shot))
    else:
        path = dir_old.joinpath('%05d.msgpk' % (shot))
    if path.is_file() and path.stat().st_size > 10:
        with open(path, 'rb') as file:
            data = [v[1] for v in msgpack.unpackb(file.read())]
            if len(data) > 50:
                for i in range(6, len(data)):
                    print('%05d %d %.4e' % (shot, (i+1), data[i]))


print('Code ok')
