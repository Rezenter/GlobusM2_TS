import json

filename = 'v:\\data\\db\\calibration\\expected\\2023.10.06_new.json'

with open(filename, 'r') as file:
    data = json.load(file)

    for i in range(len(data['T_arr'])):
        line = '%.2f ' % data['T_arr'][i]
        for ch in range(5):
            line += '%d ' % data['poly'][4]['expected'][ch][i]
        print(line[:-1])
