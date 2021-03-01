import selden
import sp_cal
import matplotlib.pyplot as plt
import json

wl_start = 700
wl_stop = 1100
wl_step = 1

T_start = 1
T_stop = 2500
T_mult = 1.1

print('Calculating kappa...')
kappa = sp_cal.SpCal('2020.11.11', '2020.11.12', wl_start, wl_stop, wl_step)
print('Done.')


def integrate(x, y):
    res = 0.0
    if len(x) != len(y):
        fuckOff
    for ind in range(len(x) - 1):
        res += (y[ind] + y[ind + 1]) * 0.5 * (x[ind + 1] - x[ind])
    return res


temp = []
current_temp = T_start
while current_temp <= T_stop:
    temp.append(current_temp)
    current_temp *= T_mult

wl_arr = []
current_wl = wl_start
while current_wl <= wl_stop:
    wl_arr.append(current_wl)
    current_wl += wl_step


result = {
    'wl_start': wl_start,
    'wl_stop': wl_stop,
    'wl_step': wl_step,
    'T_start': T_start,
    'T_stop': T_stop,
    'T_mult': T_mult,
    'T_arr': temp,
    'poly': []
}
for poly in range(10):
    cross = selden.Selden(poly, '2020.11.20')
    expected = [[] for ch in range(5)]
    for ch in range(5):
        for T in temp:
            integrand = []
            for wl in wl_arr:
                integrand.append(kappa.rel_sens(poly, ch + 1, wl) * cross.scat_power_dens(T, wl))
                #integrand.append(kappa.rel_sens(poly, ch + 1, wl))
            expected[ch].append(integrate(wl_arr, integrand))
        plt.plot(temp, expected[ch])
    result['poly'].append({
        'ind': poly,
        'expected': expected
    })
    plt.title('Poly %d' % poly)
    plt.xlim(0, T_stop)
    plt.ylim(0, 0.2)
    plt.xlabel('Temperature, eV')
    plt.ylabel('Nexpected, a.u.')
    plt.savefig('figs/poly%d.png' % poly)
    print('processed %d' % poly)
    #plt.show()
    plt.close()
with open('out/expected.json', 'w') as out_file:
    json.dump(result, out_file)
