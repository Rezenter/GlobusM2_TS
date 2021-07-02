file_name = 'excel.csv'
window = 5

lines = []
with open('in/%s' % file_name, 'r') as file:
    for line in file:
        lines.append([float(v) for v in line.split(',')])

if len(lines) < window:
    fuck_off

with open('out/%s' % file_name, 'w') as file:
    curr = [0 for col in range(len(lines[0]))]
    for i in range(window):
        for col in range(len(lines[0])):
            curr[col] += lines[i][col]
    for line_ind in range(2, len(lines) - 3):
        line = ''
        for col in range(len(lines[0])):
            line += '%f ' % (curr[col] / window)
            curr[col] += lines[line_ind + 3][col] - lines[line_ind - 2][col]
        file.write(line[:-1] + '\n')
    line = ''
    for col in range(len(lines[0])):
        line += '%f ' % (curr[col] / window)
    file.write(line[:-1])
print('Code OK')
