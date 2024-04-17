from pathlib import Path

shotn: int = 44435
#shotn: int = 41095

path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\' % shotn)
if not path.is_dir():
    fuck

files: list[str] = ['_n(R).csv', '_P(R).csv', '_T(R).csv']
times: list[float] = []
R_sep: list[float] = []
with open(path.joinpath('%05d_dynamics.csv' % shotn), 'r') as file:
    header: list[str] = file.readline().split(', ')
    time_col_ind: int = header.index('time')
    Rsep_col_ind: int = header.index('R_sep')
    file.readline()
    for line in file:
        split: list[str] = line.split(', ')
        times.append(float(split[time_col_ind]))
        R_sep.append(float(split[Rsep_col_ind]) * 10)

for filename in files:
    out: str = 'R, '
    out_heap: str = 'shotn, time, R, R_sep, R-Rsep, %s, err\n' % filename
    out_heap += '#, ms, mm, mm, mm, ??, ??\n'
    with open(path.joinpath('%05d%s' % (shotn, filename)), 'r') as file:
        header: list[str] = file.readline().split(', ')
        skip: int = 0
        while(len(header) - 1 != (len(times) + skip) * 2):
            #print(len(header) - 1, (len(times) + skip) * 2)
            skip += 1
        units: str = 'mm, '
        units_old: list[str] = file.readline().split(', ')
        for event_ind in range(len(times)):
            out += 'R-Rsep, %.2f, err, ' % times[event_ind]
            units += 'mm, %s, %s, ' % (units_old[1], units_old[1])
        out = out[:-2] + '\n' + units[:-2] + '\n'
        for line in file:
            data: list[str] = line[:-1].split(', ')
            R = float(data[0])
            out += data[0] + ', '
            if skip:
                data = data[skip * 2:]
            for event_ind in range(len(times)):
                out += '%.2f, %s, %s, ' % (R-R_sep[event_ind], data[1 + event_ind * 2], data[2 + event_ind * 2])
                'shotn, time, R, R_sep, R-Rsep, %s, err'
                out_heap += '%d, %.1f, %d, %d, %d, %s, %s\n' % (shotn, times[event_ind], R, R_sep[event_ind], R-R_sep[event_ind], data[1 + event_ind * 2], data[2 + event_ind * 2])
            out = out[:-2] + '\n'
    with open(path.joinpath('%05d_Rsep_%s' % (shotn, filename)), 'w') as file:
        file.write(out)
    with open(path.joinpath('%05d_Rsep_heap_%s' % (shotn, filename)), 'w') as file:
        file.write(out_heap)
print('Code OK')
