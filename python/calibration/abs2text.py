import json

names = [
'2026.01.16_mask',
'2026.03.31_mask_1.6_300',
'2026.03.31_mask_3_300',
'2026.03.31_mask_3_330',
'2026.03.31_mask_1.6_330',
'2026.03.31_mask_swapp_3_330'
]

p = 'd:\\data\\db\\calibration\\abs\\processed\\'
config_path = 'd:\\data\\db\\config_cpp\\2026.03.31_CTSn_mask_330.json'

config = None
with open(config_path, 'r') as file:
    config = json.load(file)

fibers = {}
for fiber in config['fibers']:
    fibers[fiber] = []

for name in names:
    calibr = None
    with open(p+name+'.json', 'r') as file:
        calibr = json.load(file)
    for ser in calibr['A']:
        fib = 'fuck'
        for poly in config['poly']:
            if '%d'%poly['serial'] == ser:
                fib = poly['fiber']
                break
        if fib == 'fuck':
            fuck
        fibers[fib].append(calibr['A'][ser])

for fiber in fibers:
    line = fiber + ' '
    for i in fibers[fiber]:
        line += '%e ' % i
    print(line)