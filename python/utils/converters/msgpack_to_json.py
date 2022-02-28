import msgpack
from pathlib import Path
import json

path = Path('0.msgpk')

original = []
with path.open(mode='rb') as file:
    data = msgpack.unpackb(file.read())

    with open('dump.json', 'w') as dump:
        json.dump(data, dump)

print('Code OK')
