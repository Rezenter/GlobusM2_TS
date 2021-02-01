import json

shotn = 389

with open('%05d.json' % shotn, 'r') as fp:
    data = json.load(fp)
    for ind in data['A']:
        print(data['A'][ind])