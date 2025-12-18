import msgpack
from pathlib import Path
import statistics

# !!! export as ADC registers
# convert to volts: (offset = 1100)
# self.header['boards'][board_ind]['offset'] - 1250 + v * 2500 / 4096

for shotn in range(46601, 46602):
    print(shotn)
    #path = Path('d:/data/db/debug/raw/%05d/0.msgpk' % shotn)
    path = Path('d:/data/db/plasma/raw/%05d/7.msgpk' % shotn)
    with path.open(mode='rb') as file:
        data = msgpack.unpackb(file.read())

        with open('out/%05d.csv' % shotn, 'w') as out:
            for event in data:
                line = ', '.join(['%.2f' % v for v in event['ch'][3]])
                out.write(line + '\n')
                for ch in range(16):
                    tmp = statistics.stdev(event['ch'][ch][:100])
                    print(tmp)
                    if tmp < 1:
                        print(event, ch)
print('Code OK')
