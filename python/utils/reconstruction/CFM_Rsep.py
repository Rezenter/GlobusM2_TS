import json

shotn = 42857


with open('\\\\172.16.12.127\\Pub\\!!!CURRENT_COIL_METHOD\\V3_zad7_mcc\\mcc_%d.json' % shotn, 'r') as mcc_file:
    data = json.load(mcc_file)
if data is None:
    fuck

#for i in range(len(data['time']['variable'])):
#    print(data['time']['variable'][i], data['ra']['variable'][i])

lp = []
with open('in/lp.csv', 'r') as file:
    for line in file:
        spl = line.split(',')
        lp.append([float(spl[0]), float(spl[1])])

elms = [
    0.18917,
    0.189366,
    0.189423,
    0.18988,
    0.190532,
    0.191047,
    0.191512,
    0.192442,
    0.192963
]

for dat in lp:
    for elm in elms:
        if elm+2e-6 <= dat[0] <= elm + 10e-6:
            ind = 0
            dist = 999
            for i in range(len(data['time']['variable'])):
                curr = abs(data['time']['variable'][i] - dat[0])
                if curr < dist:
                    dist = curr
                    ind = i
            print(data['time']['variable'][ind], 10*data['ra']['variable'][ind], elm, dat[0], dat[1])
            break

print('\n\n\n')
base = [
    [0.190037, 0.190468],
    [0.190685, 0.190988],
    [0.191174, 0.191442],
    [0.191612, 0.191443],
    [0.191632, 0.191903],
    [0.192109, 0.192407],
    [0.192602, 0.192942]
]

for dat in lp:
    for elm in base:
        if elm[0] <= dat[0] <= elm[1]:
            ind = 0
            dist = 999
            for i in range(len(data['time']['variable'])):
                curr = abs(data['time']['variable'][i] - dat[0])
                if curr < dist:
                    dist = curr
                    ind = i
            #print(data['time']['variable'][ind], 10*data['ra']['variable'][ind], elm[0], elm[1], dat[0], dat[1])
            break

print("Code OK")
