import json

ophir_shotn = [
    359,
    360,
    361,
    362
]

omz = []
with open('2023.01.16_raw_330Hz_1.6J.json', 'r') as file:
    omz = json.load(file)[0]['laser_shots']

ophir = []
for shotn in ophir_shotn:
    with open('d:\data\db\calibration\energy\959905_%d.txt' % shotn, 'r') as file:
        data = file.readlines()[38: 38 + 101]
        for line in data:
            ophir.append(float(line.split()[1]))

for i in range(len(omz)):
    print('%.3e %.3e' % (ophir[i], omz[i]))