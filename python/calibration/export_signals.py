import json

with open('2023.01.16_raw_330Hz_1.6J_G2.json', 'r') as file:
    data = json.load(file)[0]

    for pulse_ind in range(len(data['laser_shots'])):
        line = '%.1f ' % (data['laser_shots'][pulse_ind])
        for poly_ind in range(11):
            line += '%.1f ' % (data['poly'][poly_ind][0]['signals'][pulse_ind])
        print(line[:-1])