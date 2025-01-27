from pathlib import Path

dir: Path = Path('a:\\home\\user\\soft\\astra\\ASTRA_7.02\\user\\dat')


line:str = ''

header: str = ''
skip: int = 0

isTime: bool = False
const_names: list[str] = []
consts: list = []

rad_names: list[str] = []
rads: list[list] = []
rad_count: int = 0

count: int = 0

filename: Path = list(dir.glob('*.1'))[0]

with open(filename, 'r') as f:
    for line in f:
        if len(header) == 0:
            header = line
            continue

        if line.strip().startswith('==='):
            skip = 7
            continue

        if skip > 0:
            skip -= 1
            continue

        if line.strip().startswith('Time'):
            isTime = True
            const_names.extend([i.strip() for i in line.strip().split()[1:]])
            continue

        if isTime:
            isTime = False
            #print([i.strip() for i in line.strip().split()[1:]])
            #consts.extend([float(i.strip()) for i in line.strip().split()[1:]])

            while line.find('- ') >= 0:
                line = line.replace('- ', ' -')

            for val in [i.strip() for i in line.strip().split()[1:]]:
                if val.find('>') >= 0 or val.find('<') >= 0:
                    consts.append('--')
                    continue
                ind = val.find('-', 1)
                if ind > 0:
                    val = val[:ind] + 'E' + val[ind:]
                consts.append('%.3e' % float(val))
            continue

        if line.strip().startswith('a'):
            count = 0
            if rad_count == 0:
                rad_names.extend([i.strip() for i in line.strip().split()])
            else:
                rad_names.extend([i.strip() for i in line.strip().split()[1:]])
            rad_count += 1
            continue

        if rad_count == 1:
            #rads.append([float(i.strip()) for i in line.strip().split()])
            curr = []
            while line.find('- ') >= 0:
                line = line.replace('- ', ' -')
            for val in [i.strip() for i in line.strip().split()]:
                if val.find('>') >= 0 or val.find('<') >= 0:
                    curr.append('--')
                    continue
                ind = val.find('-', 1)
                if ind > 0:
                    val = val[:ind] + 'E' + val[ind:]
                curr.append('%.3e' % float(val))
            rads.append(curr)
        else:
            #rads[count] = [float(i.strip()) for i in line.strip().split()[1:]]
            curr = []
            curr = []
            while line.find('- ') >= 0:
                line = line.replace('- ', ' -')
            for val in [i.strip() for i in line.strip().split()[1:]]:
                if val.find('>') >= 0 or val.find('<') >= 0:
                    curr.append('--')
                    continue
                ind = val.find('-', 1)
                if ind > 0:
                    val = val[:ind] + 'E' + val[ind:]

                curr.append('%.3e' % float(val))
            rads[count].extend(curr)
        count += 1

with open('%s_const.txt' % filename, 'w') as out:
    out.write(header)
    out.write(', '.join(const_names))
    out.write('\n')
    out.write(', '.join(consts))

with open('%s_radial.txt' % filename, 'w') as out:
    out.write(header)
    out.write(', '.join(rad_names))
    out.write('\n')
    for line in rads:
        out.write(', '.join(line))
        out.write('\n')
print('OK')
