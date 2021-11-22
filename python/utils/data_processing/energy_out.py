import json

shot = 41001

'''with open('in/%d.json' % shot, 'r') as file:
    data = json.load(file)
    for event in data['events']:
        if 'energy' in event:
            print('%.2f %.3f' % (event['timestamp'], event['energy']))
'''

with open('in/%d_ophir.txt' % shot, 'r') as file:
    count = 38
    for line in file:
        if count > 0:
            count -= 1
            continue
        print(line.split()[1])
