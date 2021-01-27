import json
import matplotlib.pyplot as plt
import math

shotn = 39629
event_ind = 62

theta_count = 360
r42 = 42
gamma_shift = 1

with open('d:/data/db/plasma/result/%05d/%05d.json' % (shotn, shotn), 'r') as ts_fp:
    ts = json.load(ts_fp)
if ts is None:
    fuck

with open('y:/!!!CURRENT_COIL_METHOD/mcc_%d.json' % shotn, 'r') as mcc_file:
    data = json.load(mcc_file)
if data is None:
    fuck

requested_time = ts['events'][event_ind]['timestamp'] * 0.001
timestamps = data['time']['variable']

t_ind = 0
for t_ind in range(len(timestamps) - 1):
    if timestamps[t_ind] <= requested_time < timestamps[t_ind + 1]:
        if (requested_time - timestamps[t_ind]) >= (timestamps[t_ind + 1] - requested_time):
            t_ind += 1
        break

last = {
    'R': data['boundary']['rbdy']['variable'][t_ind],
    'z': data['boundary']['zbdy']['variable'][t_ind]
}

if data['boundary']['leg_ex']['variable'][t_ind]:
    last['R'] = [el for el in reversed(data['boundary']['rleg_1']['variable'][t_ind])]
    last['z'] = [el for el in reversed(data['boundary']['zleg_1']['variable'][t_ind])]

    last['R'].append(data['Rx']['variable'][t_ind])
    last['z'].append(data['Zx']['variable'][t_ind])

    last['R'].extend(data['boundary']['rbdy']['variable'][t_ind])
    last['z'].extend(data['boundary']['zbdy']['variable'][t_ind])

    last['R'].append(data['Rx']['variable'][t_ind])
    last['z'].append(data['Zx']['variable'][t_ind])

    last['R'].extend(data['boundary']['rleg_2']['variable'][t_ind])
    last['z'].extend(data['boundary']['zleg_2']['variable'][t_ind])
else:
    last['R'] = data['boundary']['rbdy']['variable'][t_ind]
    last['z'] = data['boundary']['zbdy']['variable'][t_ind]

plt.plot(last['R'], last['z'])
plt.vlines(
    [data['R']['variable'][t_ind]],
    data['Z']['variable'][t_ind] - 1,
    data['Z']['variable'][t_ind] + 1,
    colors=['green'])
plt.hlines(
    [data['Z']['variable'][t_ind]],
    data['R']['variable'][t_ind] - 1,
    data['R']['variable'][t_ind] + 1,
    colors=['green'])

r_cw = 0
z_cw = 0
summ = 0
for curr_ind in range(int(data['nj']['variable'][t_ind])):
    summ += data['current_coils']['I']['variable'][t_ind][curr_ind]
    r_cw += data['current_coils']['I']['variable'][t_ind][curr_ind] * data['current_coils']['r']['variable'][t_ind][curr_ind]
    z_cw += data['current_coils']['I']['variable'][t_ind][curr_ind] * data['current_coils']['z']['variable'][t_ind][curr_ind]
r_cw /= summ
z_cw /= summ

plt.vlines(
    [r_cw],
    z_cw - 1,
    z_cw + 1,
    colors=['magenta'])
plt.hlines(
    [z_cw],
    r_cw - 1,
    r_cw + 1,
    colors=['magenta'])
plt.vlines([r42], -50, 50)
plt.hlines([0], 0, 70)
#print('geom:', data['R']['variable'][t_ind], data['Z']['variable'][t_ind])
#print('/summ', r_cw / summ, z_cw / summ, data['zav']['variable'][t_ind])
#print('/val', r_cw /data['Ipl']['variable'][t_ind], z_cw / data['Ipl']['variable'][t_ind], data['zav']['variable'][t_ind])

chord = {
    'up': [],
    'down': [],
    'mid': {}
}

for poly_ind in range(len(ts['polys'])):
    r = ts['polys'][poly_ind]['R'] * 0.1
    R = []
    Z = []

    theta_poly = math.atan(-z_cw / (r - r_cw))

    a = math.sqrt(math.pow(z_cw, 2) + math.pow(r - r_cw, 2))

    c0 = z_cw / math.sin(theta_poly)
    c2 = (data['kx']['variable'][t_ind] - 1) / data['a']['variable'][t_ind]
    #a = (-1 + math.sqrt(1 - 4 * c2 * c0)) / (2 * c2)

    shift = \
        (r_cw - data['R']['variable'][t_ind]) * \
        math.pow((1 - math.pow(a / data['a']['variable'][t_ind], 2)), gamma_shift)
    triang = a * data['de']['variable'][t_ind] / data['a']['variable'][t_ind]
    elong = 1 + a * (data['kx']['variable'][t_ind] - 1) / data['a']['variable'][t_ind]

    #print(data['R']['variable'][t_ind], shift, a * (math.cos(0) - triang * math.pow(math.sin(0), 2)))
    #print('   ',  a * (math.cos(0)), a*triang * math.pow(math.sin(0), 2) )

    for theta_ind in range(theta_count + 1):
        theta = math.pi * theta_ind * 2 / theta_count

        R.append(
            data['R']['variable'][t_ind] + shift + a * (math.cos(theta) - triang * math.pow(math.sin(theta), 2))
        )
        Z.append(z_cw + a * elong * math.sin(theta))

    for i in range(theta_count):
        if R[i] <= r42 < R[i + 1]:
            chord['down'].append({
                'poly': poly_ind,
                'z': Z[i] + (r42 - R[i]) * (Z[i + 1] - Z[i]) / (R[i + 1] - R[i])
            })
        elif R[i] > r42 >= R[i + 1]:
            chord['up'].append({
                'poly': poly_ind,
                'z': Z[i] + (r42 - R[i]) * (Z[i + 1] - Z[i]) / (R[i + 1] - R[i])
            })

    if r < r42:
        closest = True
        for ind_possible in range(len(ts['polys'])):
            r_possible = ts['polys'][ind_possible]['R'] * 0.1
            if r42 >= r_possible > r:  # check for bad points
                closest = False
                break
        if closest:
            chord['mid']['in'] = poly_ind
    if r > r42:
        closest = True
        for ind_possible in range(len(ts['polys'])):
            r_possible = ts['polys'][ind_possible]['R'] * 0.1
            if r42 <= r_possible < r:  # check for bad points
                closest = False
                break
        if closest:
            chord['mid']['out'] = poly_ind

    plt.plot(R, Z)

    # show integral
#print(chord)

plt.title('#%d timestamp %.1f ms' % (shotn, timestamps[t_ind] * 1000))
plt.xlim(0, 65)
plt.ylim(-50, 50)
plt.xlabel('R, cm')
plt.ylabel('Z, cm')
#plt.savefig('figs/poly%d.png' % poly)
#print('processed %d' % poly)
plt.show()
plt.close()

profile = {
    'val': [],
    'z': []
}

points = chord['down']
points.append({'mid': True})
points.extend(reversed(chord['up']))
for p in points:
    if 'mid' in p and p['mid']:
        profile['z'].append(0)
        t_i = ts['events'][event_ind]['T_e'][chord['mid']['in']]['n']
        t_o = ts['events'][event_ind]['T_e'][chord['mid']['out']]['n']
        r_i = ts['polys'][chord['mid']['in']]['R'] * 0.1
        r_o = ts['polys'][chord['mid']['out']]['R'] * 0.1
        profile['val'].append(t_o + (r_o - r42) * (t_i - t_o) / (r_o - r_i))
    else:
        profile['z'].append(p['z'])
        profile['val'].append(ts['events'][event_ind]['T_e'][p['poly']]['n'])
#print(profile)
plt.plot(profile['z'], profile['val'], marker='o', linestyle='solid')
plt.title('n_e at R=%d, #%d timestamp %.1f ms' % (r42, shotn, timestamps[t_ind] * 1000))
plt.xlim(-50, 50)
plt.ylim(0, 1e17)
plt.xlabel('Z, cm')
plt.ylabel('n_e, eV')
#plt.savefig('figs/poly%d.png' % poly)
#print('processed %d' % poly)
plt.show()
plt.close()

print('ok')
