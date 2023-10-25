from pathlib import Path
import struct

res_data_path: str = 'out/'
raw_data_path: Path = Path('d:/data/T15/Raman/21 syn/2023-10-24_14-05-13')

photodiode_ch: int = 1
dump_first: int = 4
int_from_cell: int = 40
int_to_cell: int = 180

def __bin_to_JSON(path_in: Path) -> list:
    data: list = []
    with path_in.open(mode='rb') as file:
        raw = file.read()
        count = len(raw) / (8 * 1024 * 4 + 8)
        #print(len(raw))
        if not int(count) == count:
            fuck
        count = int(count)

        for event_ind in range(count):
            event = {
                't': struct.unpack_from('L', raw, (count * (8 * 1024 * 4)) + 8 * event_ind)[0],
                'sig': struct.unpack_from('1024f', raw, (event_ind * (8 * 1024 * 4)) + photodiode_ch * 1024 * 4)
            }
            data.append(event)
        #print(count * (8 * 1024 * 4 + 8))
    return data

data_in = __bin_to_JSON(raw_data_path)
for event in data_in:
    zero: float = sum(event['sig'][dump_first: int_from_cell])/(int_from_cell-dump_first)
    integral: float = sum(event['sig'][int_from_cell: int_to_cell]) - zero * (int_to_cell-int_from_cell)
    print(event['t'] * 1e-3, zero, integral)

print('\n\n')
for i in range(int_from_cell, int_to_cell):
    line: str = '%d ' % i
    for event in data_in:
        line += '%.4f ' % (event['sig'][i] - sum(event['sig'][dump_first: int_from_cell])/(int_from_cell-dump_first))
    print(line)
