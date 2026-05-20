import json

top_name = 'd:\\data\\db\\calibration\\expected\\2026.01.23_masked.json'
bot_name = 'd:\\data\\db\\calibration\\expected\\2026.04.01_masked_raw.json'

top = None
bot = None

with open(top_name, 'r') as file:
    top = json.load(file)

with open(bot_name, 'r') as file:
    bot = json.load(file)

line = ''
for poly in top['poly']:
    line += top['poly'][poly]['fiber'] + ' '
print(line)

for ch in range(5):
    line = ''
    for poly in top['poly']:
        line += '%f ' % (top['poly'][poly]['ae'][ch]/bot['poly'][poly]['ae'][ch])
    print(line)