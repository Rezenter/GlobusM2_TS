from pathlib import Path

#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\1 loc low\\7\\ne=exp+anomaly\\OH_LOC_low_anomaly.data.OH.model.1'
#filename: str = 'd:\\data\\globus\\calc\\OH\\results\\runs\\1 loc low\\7\\ne=exp, Zeff=1\\OH_LOC_low_Zeff.data.OH.model.1'

#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\1.5 loc med\\anomaly\\OH_loc_med_anomaly.data.OH.model.1'
#filename: str = 'd:\\data\\globus\\calc\\OH\\results\\runs\\1.5 loc med\\neo, Zeff=1.3\\OH_LOC_med_Zeff.data.OH.model.1'

#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\2 loc high\\ne_ass_anomaly\\OH_LOC_high_anomaly.data.OH.model.1'

#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\2 loc high\\ne_ass_anomaly\\ano8\\OH_LOC_high_ano8.data.OH.model.1'

#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\3 soc low\\ne_ass_anomaly\\OH_SOC_low_anomaly.data.OH.model.1'
#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\3.5 soc low-med\\anomaly\\OH_SOC_l-m_ano.data.OH.model.1'
#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\4 soc med\\anomaly\\OH_SOC_med_anomaly.data.OH.model.1'
#filename: str = 'D:\\data\\globus\\calc\\OH\\results\\runs\\5 soc high\\anomaly\\OH_SOC_high_anomaly.data.OH.model.1'

#filename: str = 'd:\\data\\globus\\calc\\NBI\\ASTRA\\41114\\41114.data.NBI.model.1'
dir: Path = Path('a:\\home\\user\\soft\\astra\\ASTRA_7.02\\user\\dat')

constants: bool = False
rad: bool = False

line = ''
c_names = []
c_vars = []

filename: Path = list(dir.glob('*.1'))[0]

with open(filename, 'r') as f:
    header: str = ''
    header += f.readline()
    header += f.readline()
    with open('%s_const.txt' % filename, 'w') as out:
        out.write(header)
        while not constants:
            line = f.readline().strip()
            if line.startswith('Time'):
                c_names.extend(line.split()[1:])
                c_vars.extend(f.readline().strip().split()[1:])
            else:
                if line.startswith('a'):
                    constants = True
        out_line = ''
        for i in range(len(c_names)):
            out_line += '%s ' % c_names[i]
        out.write(out_line + '\n')
        out_line = ''
        for i in range(len(c_vars)):
            out_line += '%s ' % c_vars[i]
        out.write(out_line)
    with open('%s_radial.txt' % filename, 'w') as out:
        out.write(header)
        count: int = 0
        line = '        %s' % line
        while line.startswith('        '):
            if count != 0:
                out.write(' ')
            count += 1
            out.write(line.strip())
            line = f.readline()
        out.write('\n')
        curr: int = 0
        while True:
            if curr % count == 0:
                if curr != 0:
                    out.write('\n')
            else:
                out.write(' ')
            curr += 1
            out.write(line.strip())
            line = f.readline()
            if len(line) == 0:
                break
print('OK')
