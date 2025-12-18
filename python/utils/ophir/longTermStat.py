import msgpack
from pathlib import Path
import statistics
import datetime

dir_new: Path = Path('d:\\data\\db\\plasma\\raw\\')
dir_old: Path = Path('\\\\192.168.10.41\\d\\data\\db\\plasma\\ophir\\')

start: int = 42832
stop: int = 46381

energy = ''

for shot in range(start, stop):
    if  shot > 46155:
        path = dir_new.joinpath('%05d\\ophir.msgpk' % (shot))
    else:
        path = dir_old.joinpath('%05d.msgpk' % (shot))
    if path.is_file() and path.stat().st_size > 10:
        with open(path, 'rb') as file:
            data = [v[1] for v in msgpack.unpackb(file.read())]
            if len(data) > 50:
                date = datetime.datetime.fromtimestamp(path.stat().st_ctime)
                energy += '%s %05d %.2e %.2e\n' % (date.strftime('%d.%m.%Y %H:%M'), shot, 1e3*sum(data)/len(data), 1e3*statistics.stdev(data))

print(energy)

print('Code ok')
