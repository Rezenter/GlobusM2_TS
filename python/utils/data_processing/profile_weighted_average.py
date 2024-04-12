# expected file structure: csv: shotn, time

req_file: str = '41114'
db: str = ('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\')

request = []
with open('in/%s.csv' % req_file, 'r') as file:
    header = file.readline()[:-1].split(',')
    shotn_col = header.index('shotn')
    time_col = header.index('time')
    file.readline() # units
    for line in file:
        spl = line[:-1].split(',')
        request.append((int(spl[shotn_col]), float(spl[time_col])))

r = []
te_out = []
ne_out = []
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
        if len(r) == 0:
            r = r_tmp
        else:
            for i in range(len(r)):
                if r[i] != r_tmp[i]:
                    fuck
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
        if len(r) == 0:
            r = r_tmp
        else:
            for i in range(len(r)):
                if r[i] != r_tmp[i]:
                    fuck
        ne_out.append(ne)


with open('out/%s_T(R).csv' % req_file, 'w') as file:
    line = 'R, '
    for col in te_out:
        line += '%.5d_%.1f, err, ' % (col[0])
    line += 'ave, err\n'
    file.write(line)

    for i in range(len(r)):
        line = '%d, ' % r[i]

        ave_top: float = 0
        weight_sum: float = 0
        for col in te_out:
            if col[1 + i][0] == '--':
                line += '--, --, '
                continue

            line += '%s, %s, ' % col[1 + i]
            #weight = float(col[1 + i][1]) ** -2
            weight = (float(col[1 + i][1]) / float(col[1 + i][0])) ** -2
            ave_top += float(col[1 + i][0]) * weight
            weight_sum += weight
        line += '%.1f, %.1f\n' % (ave_top / weight_sum, (1 / weight_sum) ** 0.5)

        file.write(line)

with open('out/%s_n(R).csv' % req_file, 'w') as file:
    line = 'R, '
    for col in ne_out:
        line += '%.5d_%.1f, err, ' % col[0]
    line += 'ave, err\n'
    file.write(line)

    for i in range(len(r)):
        line = '%d, ' % r[i]

        ave_top: float = 0
        weight_sum: float = 0
        for col in ne_out:
            if col[1 + i][0] == '--':
                line += '--, --, '
                continue

            line += '%s, %s, ' % col[1 + i]
            #weight = float(col[1 + i][1]) ** -2
            weight = (float(col[1 + i][1]) / float(col[1 + i][0])) ** -2
            ave_top += float(col[1 + i][0]) * weight
            weight_sum += weight
        line += '%.1f, %.1f\n' % (ave_top / weight_sum, (1 / weight_sum) ** 0.5)

        file.write(line)

for i in range(len(r)):
    line = '%d ' % r[i]

    te_top: float = 0
    te_sum: float = 0
    for col in te_out:
        if col[1 + i][0] == '--':
            continue

        te_top += float(col[1 + i][0]) / float(col[1 + i][1]) ** 2
        te_sum += float(col[1 + i][1]) ** -2

    ne_top: float = 0
    ne_sum: float = 0
    for col in ne_out:
        if col[1 + i][0] == '--':
            continue

        ne_top += float(col[1 + i][0]) / float(col[1 + i][1]) ** 2
        ne_sum += float(col[1 + i][1]) ** -2
    line += '%.1f %.1f %.2e %.2e' % (te_top / te_sum, (1 / te_sum) ** 0.5, ne_top / ne_sum, (1 / ne_sum) ** 0.5)
    print(line)

print('code OK')
