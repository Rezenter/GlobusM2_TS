import msgpack
from pathlib import Path

shotn = 46474
print(shotn)
path = Path('d:/data/db/plasma/raw/%05d/0.msgpk' % shotn)
with path.open(mode='rb') as file:
    data_cts = msgpack.unpackb(file.read())
path = Path('d:/data/db/plasma/raw/%05d/2.msgpk' % shotn)
with path.open(mode='rb') as file:
    data_dts = msgpack.unpackb(file.read())

for i in range(20):
    print(data_cts[24+3*i]['t'], data_dts[1+i]['t'])

print('Code OK')