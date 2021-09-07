import selden
import matplotlib.pyplot as plt

import filter
import qe


import sp_cal


wl_start = 700
wl_stop = 1100
wl_step = 1
print('Calculating kappa...')
kappa = sp_cal.SpCal('2020.11.11', '2020.11.12', wl_start, wl_stop, wl_step)
print('Done.')
with open('out/K_new.csv', 'w') as out_file:
    curr_wl = wl_start
    while curr_wl <= wl_stop:
        line = '%.1f ,' % curr_wl
        for ch in range(5):
            line += '%.2e, ' % kappa.rel_sens(0, ch + 1, curr_wl)
        out_file.write(line[:-2] + '\n')
        curr_wl += wl_step
exit()

fil = filter.Filters()
apd = qe.APD()

cross = selden
cross9 = selden

temp = 500  # eV
wl = 900  # nm

print(cross.scat_power_dens(temp, wl))


test_lambda = range(800, 1250)
test_temp_range = [1, 10, 100, 1000]


def integrate(x, y):
    res = 0.0
    if len(x) != len(y):
        fuckOff
    for ind in range(len(x) - 1):
        res += (y[ind] + y[ind + 1]) * 0.5 * (x[ind + 1] - x[ind])
    return res


for test_temp in test_temp_range:
    local_result = []
    l2 = []
    for wl in test_lambda:
        #print(apd.qe(wl))
        local_result.append(cross.scat_power_dens(test_temp, wl))
        l2.append(cross9.scat_power_dens(test_temp, wl))
    print(' T = %d, integral = %f' % (test_temp, integrate(test_lambda, local_result)))

    plt.plot(test_lambda, local_result)
    plt.plot(test_lambda, l2)
    plt.xlim(800, 1150)
    plt.ylim(0, 0.2)
    plt.legend(['1 eV', '10 eV', '100 eV', '1000 eV'], loc='best')
    plt.xlabel('Wavelenght, nm')
    plt.ylabel('Scattering Power')
    plt.show()




print('Ok.')
