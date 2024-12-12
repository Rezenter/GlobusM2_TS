from pathlib import Path
import json
import struct
import math

filename: str = '2024.09.04_HFS'
config_filename: str = '2024.08.30_G2-10_HFS'

path_conf: Path = Path('\\\\172.16.12.130\\d\\data\\db\\config\\%s.json' % config_filename)
path_in: Path = Path('\\\\172.16.12.130\\d\\data\\db\\calibration\\spectral\\%s\\slow\\' % filename)
#path_in: Path = Path('\\\\172.16.12.130\\d\\data\\db\\calibration\\spectral\\%s\\' % filename)
path_out: Path = Path('\\\\172.16.12.130\\d\\data\\db\\calibration\\spectral\\%s.json' % filename)
chMap = [0, 2, 4, 6, 10, 8, 14, 12, 1, 3, 5, 7, 11, 9, 15, 13]


def read_raw(config):
    data = []
    for slow_board in config['slow']:
        p: Path = path_in.joinpath('%s\\%s.slow' % (poly['fiber'], slow_board['ip']))
        if p.is_file():
            with open(path_in.joinpath('%s\\%s.slow' % (poly['fiber'], slow_board['ip'])), 'rb') as file:
                data_raw = file.read()
                point_count = int(len(data_raw) / (16 * 2))  # ch count = 16, sizeof(short) = 2
                # print(point_count, len(data))
                board = [[] for ch in range(16)]
                for ch_ind in range(16):
                    for i in range(1, point_count):  # skip first as it is sometimes corrupted
                        board[ch_ind].append(
                            struct.unpack_from('<h', buffer=data_raw, offset=16 * i * 2 + 2 * chMap[ch_ind])[0])
                data.append(board)
        else:
            data.append([[] for ch in range(16)])
            for dir in path_in.joinpath('%s\\' % poly['fiber']).glob('*'):
                p: Path = path_in.joinpath('%s\\%s.slow' % (dir, slow_board['ip']))
                if p.is_file() and p.stat().st_size > 10:
                    with open(p, 'rb') as file:
                        data_raw = file.read()
                        point_count = int(len(data_raw) / (16 * 2))  # ch count = 16, sizeof(short) = 2
                        # print(point_count, len(data))

                        for ch_ind in range(16):
                            for i in range(1, point_count):  # skip first as it is sometimes corrupted
                                data[-1][ch_ind].append(struct.unpack_from('<h', buffer=data_raw, offset=16 * i * 2 + 2 * chMap[ch_ind])[0])
                    #print(len(data[-1][ch_ind]))
                    #break #debug
                else:
                    print('bad luck')
    return data


def count_elements(seq: list[int]) -> list[int]:
    offset = min(seq)
    hist = [0 for i in range(offset, max(seq) + 1)]
    for i in seq:
        hist[i - offset] += 1
    return hist


def smooth(seq: list[int], window: int):
    smoothed = []
    current = sum(seq[:window])
    for i in range(len(seq)):
        if i > window:
            current -= seq[i - window - 1]
        if i + window < len(seq):
            current += seq[i + window]
        smoothed.append(current)
    return smoothed


def scan_distribution(seq: list[int]):
    window_mult: float = 0.5
    smooth_count: int = 3

    m_val = 0
    m_i = 0
    for i in range(len(seq)):
        if seq[i] > m_val:
            m_val = seq[i]
            m_i = i
    left_i = 0
    for i in range(len(seq)):
        if seq[i] > m_val * 0.5:
            left_i = i
            break
    right_i = 0
    for i in range(len(seq) - 1, 0, -1):
        if seq[i] > m_val * 0.5:
            right_i = i
            break

    fwhm = right_i - left_i
    result = {
        'max': m_val,
        'max_ind': m_i,
        'FWHM': fwhm,
        'smoothed': seq.copy()
    }

    window = max(1, math.floor(fwhm * window_mult))
    for i in range(smooth_count):
        result['smoothed'] = smooth(result['smoothed'], window).copy()

    m_val = 0
    m_i = 0
    for i in range(len(result['smoothed'])):
        if result['smoothed'][i] > m_val:
            m_val = result['smoothed'][i]
            m_i = i

    result['max'] = m_val
    result['max_ind'] = m_i

    return result


if not path_in.is_dir() or not path_conf.is_file():
    fuck
measurements = [str(x).split('\\')[-1] for x in path_in.iterdir() if x.is_dir()]

config = None
with open(path_conf, 'r') as file:
    config = json.load(file)

result = {
    'type': 'spectral calibration results ready for expected signals calculation',
    'version': 3,
    'config': config_filename,
    'raw_data': filename,
    'polar': True,
    'poly': []
}
for poly in config['poly']:
    print(poly['fiber'])
    fiber = config['fibers'][poly['fiber']]
    if poly['fiber'] not in measurements:
        print('no measurement found')
        continue

    data = read_raw(config)


    res_poly = {
        'ind': poly['ind'],
        'fiber': poly['fiber'],
        'min': [],
        'max': [],
        'amp': []
    }

    with open('debug/ind_%d_raw.csv' % poly['ind'], 'w') as file:
        for i in range(len(data[0][0])):
            line: str = ''
            for ch_ind in range(len(poly['channels'])):
                ch = poly['channels'][ch_ind]
                line += '%d, ' % (data[ch['slow_adc']][ch['slow_adc_ch']][i])
            file.write(line[:-2] + '\n')
    debug_data = []
    for ch_ind in range(len(poly['channels'])):
        ch = poly['channels'][ch_ind]

        histogram_raw = count_elements(data[ch['slow_adc']][ch['slow_adc_ch']])
        left = scan_distribution(histogram_raw[:math.floor(len(histogram_raw) / 2)].copy())
        right = scan_distribution(histogram_raw[math.floor(len(histogram_raw) / 2):].copy())

        '''
        ml_val = 0
        ml_i = 0
        for i in range(math.floor(len(histogram_raw) / 2)):
            if histogram_raw[i] > ml_val:
                ml_val = histogram_raw[i]
                ml_i = i

        #res_poly['min'].append(ml_i)
        '''
        res_poly['min'].append(left['max_ind'])

        '''
        mr_val = 0
        mr_i = 0
        for i in range(len(histogram_raw) - 1, math.floor(len(histogram_raw) / 2), -1):
            if histogram_raw[i] > mr_val:
                mr_val = histogram_raw[i]
                mr_i = i
        #res_poly['max'].append(mr_i)
        '''
        res_poly['max'].append(right['max_ind'] + math.floor(len(histogram_raw) / 2))

        #res_poly['amp'].append((res_poly['max'][-1] - res_poly['min'][-1]) / ch['slow_gain'])
        res_poly['amp'].append(res_poly['max'][-1] - res_poly['min'][-1])

        #print(' ', ml_i - left['max_ind'],  mr_i - right['max_ind'] - math.floor(len(histogram_raw) / 2))
        # [hist[i] + hist[i+1] for i in range(len(hist) - 1)]

        #debug_data.append(histogram_raw)
        #left['smoothed'].extend(right['smoothed'])
        #debug_data.append(left['smoothed'])

    '''
    with open('debug/ind_%d_histogram.csv' % poly['ind'], 'w') as file:
        wait: bool = True
        ind: int = 0
        while wait:
            wait = False
            line: str = ''
            for ch in debug_data:
                if ind < len(ch):
                    wait = True
                    line += '%d, ' % ch[ind]
                else:
                    line += '--, '
            file.write(line[:-2] + '\n')
            ind += 1
    '''
    result['poly'].append(res_poly)


with open(path_out, 'w') as file:
    json.dump(result, file, indent=2)

print('OK')
