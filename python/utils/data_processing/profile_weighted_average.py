# expected file structure: csv: shotn, time

#req_file: str = 'request'
#req_file: str = 'NBI_profiles_4KTM'
#req_file: str = 'OH_profiles_4KTM'

req_file: str = 'Ip300_Bt07_250-400'
db: str = ('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\')

request = []
with open('in/%s.csv' % req_file, 'r') as file:
    header = file.readline()[:-1].split(',')
    #shotn_col = header.index('shotn')
    shotn_col = header.index('shot#')
    time_col = header.index('time')
    file.readline() # units
    for line in file:
        spl = line.split(',')
        request.append((int(float(spl[shotn_col])), float(spl[time_col])*1e3))

r = []
te_out = []
ne_out = []
te_dict = {}
ne_dict = {}
for req in request:
    with open('%s%05d\\%05d_T(R).csv' % (db, req[0], req[0])) as file:
        header = file.readline().split(', ')
        time_col = header.index('%.1f' % req[1])
        te = [req]
        r_tmp = []

        file.readline()
        for line in file:
            spl = line.split(', ')
            r_tmp.append(float(spl[0]))
            te.append((spl[time_col].strip(), spl[time_col + 1].strip()))

        for i in range(len(r_tmp)):
            if r_tmp[i] not in te_dict:
                te_dict[r_tmp[i]] = []
            if te[i+1][0] != '--':
                te_dict[r_tmp[i]].append(te[i+1])
        if len(r) == 0:
            r = r_tmp
        else:
            for i in range(len(r)):
                if len(r_tmp) == i or r[i] != r_tmp[i]:
                    r_tmp.insert(i, r[i])
                    te.insert(i, ('--', '--'))
                    #fuck
        te_out.append(te)

    with open('%s%05d\\%05d_n(R).csv' % (db, req[0], req[0])) as file:
        header = file.readline().split(', ')
        time_col = header.index('%.1f' % req[1])
        ne = [req]
        r_tmp = []

        file.readline()
        for line in file:
            spl = line.split(', ')
            r_tmp.append(float(spl[0]))
            ne.append((spl[time_col].strip(), spl[time_col + 1].strip()))
        for i in range(len(r_tmp)):
            if r_tmp[i] not in ne_dict:
                ne_dict[r_tmp[i]] = []
            if ne[i+1][0] != '--':
                ne_dict[r_tmp[i]].append(ne[i+1])
        if len(r) == 0:
            r = r_tmp
        else:
            for i in range(len(r)):
                if len(r_tmp) == i or r[i] != r_tmp[i]:
                    r_tmp.insert(i, r[i])
                    ne.insert(i, ('--', '--'))
        ne_out.append(ne)


with open('out/%s_T(R).csv' % req_file, 'w') as file:
    line = 'R, '
    for col in te_out:
        line += '%.5d_%.1f, err, ' % (col[0])

    file.write(line[:-2] + '\n')

    for i in range(len(r)):
        line = '%d, ' % r[i]

        for col in te_out:
            if col[1 + i][0] == '--':
                line += '--, --, '
                continue

            line += '%s, %s, ' % col[1 + i]

        file.write(line[: -2] + '\n')

with open('out/%s_n(R).csv' % req_file, 'w') as file:
    line = 'R, '
    for col in ne_out:
        line += '%.5d_%.1f, err, ' % col[0]

    file.write(line[:-2] + '\n')

    for i in range(len(r)):
        line = '%d, ' % r[i]

        for col in ne_out:
            if col[1 + i][0] == '--':
                line += '--, --, '
                continue

            line += '%s, %s, ' % col[1 + i]
            #weight = float(col[1 + i][1]) ** -2


        file.write(line[:-2] + '\n')

for r in te_dict:
    r_te = te_dict[r]
    r_ne = ne_dict[r]

    line = '%d ' % r

    te_top: float = 0
    te_sum: float = 0
    for pair in r_te:
        te_top += float(pair[0]) / float(pair[1]) ** 2
        te_sum += float(pair[1]) ** -2

    ne_top: float = 0
    ne_sum: float = 0
    for pair in r_ne:
        ne_top += float(pair[0]) / float(pair[1]) ** 2
        ne_sum += float(pair[1]) ** -2
    line += '%.1f %.1f %.2e %.2e' % (te_top / te_sum, (1 / te_sum) ** 0.5, ne_top / ne_sum, (1 / ne_sum) ** 0.5)
    print(line)

print('code OK')
