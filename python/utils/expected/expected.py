import selden
import sp_cal
import matplotlib.pyplot as plt
import json

lambda0 = 1064.4
lambda0 = 1047.6

aux_filter = 'zs-10.csv'  # WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
aux_filter = None

wl_start = 700
wl_stop = 1099
wl_step = 1

T_start = 1
T_stop = 2500
T_mult = 1.02
T_mult = 1.1

print('Calculating kappa...')
kappa = sp_cal.SpCal('2020.11.11', '2020.11.12', wl_start, wl_stop, wl_step, additional_filter=aux_filter)
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

if aux_filter is None:
    aux_name = "None"
else:
    aux_name = aux_filter

result = {
    'lambda_0': lambda0,
    'wl_start': wl_start,
    'wl_stop': wl_stop,
    'wl_step': wl_step,
    'T_start': T_start,
    'T_stop': T_stop,
    'T_mult': T_mult,
    'aux filter': aux_name,
    "J_from_int": 6.7e-05,  # placeholder
    'T_arr': temp,
    'poly': []
}


def dump_kappa(poly):
    integrated = [0 for i in range(5)]
    for wl_ind in range(len(wl_arr) - 1):
        wl = wl_arr[wl_ind]
        line = '%.1f ' % wl
        for ch in range(5):
            line += '%.3f ' % kappa.rel_sens(poly, ch + 1, wl)
            integrated[ch] += (kappa.rel_sens(poly, ch + 1, wl_arr[wl_ind]) + kappa.rel_sens(poly, ch + 1, wl_arr[
                wl_ind + 1])) * 0.5 * (wl_arr[wl_ind + 1] - wl_arr[wl_ind])
        print(line[:-1])
    print()
    print(integrated)


def dump_spectrum(poly, config, T):
    cross = selden.Selden(poly, config, lambda0)
    for wl in wl_arr:
        print('%.1f %.5f' % (wl, cross.scat_power_dens(T, wl)))


def dump_expected(expected):
    for t_ind in range(len(temp)):
        line = '%.2e ' % temp[t_ind]
        for ch in expected:
            line += '%.4e ' % ch[t_ind]
        print(line[:-1])


#dump_kappa(8)  # tmp
poly = 4
#for ch in range(5):
#    print(kappa.kappa(poly, ch + 1))
print('\n\n')
dump_spectrum(poly, '2020.11.20', 500)
fuck

for poly in range(10):
    print('processing poly %d...' % poly)
    #poly = 8
    cross = selden.Selden(poly, '2020.11.20', lambda0)
    expected = [[] for ch in range(5)]
    for ch in range(5):
        for T in temp:
            integrand = []
            for wl in wl_arr:
                integrand.append(kappa.rel_sens(poly, ch + 1, wl) * cross.scat_power_dens(T, wl))

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
    #dump_expected(expected)
with open('out/expected.json', 'w') as out_file:
    json.dump(result, out_file)
print('OK')
