import msgpack
from pathlib import Path

for shotn in range(779, 795):
    print(shotn)
    path = Path('d:/data/db/debug/raw/%05d/0.msgpk' % shotn)
    with path.open(mode='rb') as file:
        data = msgpack.unpackb(file.read())

        with open('out/%05d.csv' % shotn, 'w') as out:
            for event in data:
                line = ', '.join(['%.2f' % v for v in event['ch'][0]])
                out.write(line + '\n')

print('Code OK')
