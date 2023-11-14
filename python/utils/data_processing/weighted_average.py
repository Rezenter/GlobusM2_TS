# expected file structure: csv X|Y|Yerr|Y|Yerr...

header_count: int = 0

with open('c:\\Users\\nz\\Downloads\\ne.csv', 'r') as file_in:
    for line in file_in:
        if header_count != 0:
            hea                                                                                                                                                                                                                                                                                                                                                                         der_count -= 1
        else:
            spl = line.split(',')
            if len(spl) % 2 == 0:
                print('Wrong column count')
                fuck
            out: str = spl[0]
            ave_top: float = 0
            weight_sum: float = 0
            for col in range(1, len(spl), 2):
                if spl[col] == '--':
                    continue
                ave_top += float(spl[col]) / float(spl[col+1])**2
                weight_sum += float(spl[col+1])**-2
            out += ' %.3e %.3e' % (ave_top/weight_sum, (1/weight_sum)**0.5)
            print(out)

print('Code OK')
