import json

shotn = 40033

with open('\\\\172.16.12.127\\Pub\\!!!CURRENT_COIL_METHOD\\V3_zad7_mcc\\mcc_%d.json' % shotn,'r') as f:
    data = json.load(f)['shafr_int_method']

for i in range(len(data['time']['variable'])):
    print(data['time']['variable'][i], data['w_eq']['variable'][i])
print('\n\nOK')