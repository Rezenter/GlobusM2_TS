import json
import phys_const

path: str = '\\\\172.16.12.127\\Pub\\!!!CURRENT_COIL_METHOD\\V3_zad7_mcc\\'

with open('in\\request.csv', 'r') as req_file:
    opened: int = 0
    cfm_file = None
    ind: int = 0
    for line in req_file:
        spl = line.split(',')
        shotn: int = int(spl[0])
        time: float = float(spl[1])

        if shotn != opened:
            with open('%smcc_%05d.json' % (path, shotn), 'r') as file:
                cfm_file = json.load(file)
                ind = 0
        while (cfm_file['shafr_int_method']['time']['variable'][ind + 1] < time):
            ind += 1
        val = phys_const.interpolate(x_prev=cfm_file['shafr_int_method']['time']['variable'][ind], x_next=cfm_file['shafr_int_method']['time']['variable'][ind + 1],
                                     x_tgt=time,
                                     y_prev=cfm_file['shafr_int_method']['w_eq']['variable'][ind], y_next=cfm_file['shafr_int_method']['w_eq']['variable'][ind + 1])
        print(val)
print('OK')
