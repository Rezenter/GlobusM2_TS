import sp_cal

wl_start = 400
wl_stop = 1099
wl_step = 1

wl_arr = []
current_wl = wl_start
while current_wl <= wl_stop:
    wl_arr.append(current_wl)
    current_wl += wl_step

print('Calculating old kappa...')
kappa_old = sp_cal.SpCal(calibr_filename='2020.11.11', config_filename='2020.11.12',
                     wl_start=wl_start, wl_stop=wl_stop, wl_step=wl_step, additional_filter=None)
print('Calculating new kappa...')
kappa_new = sp_cal.SpCal(calibr_filename='2022.05.06', config_filename='2021.11.24_g2-10',
                     wl_start=wl_start, wl_stop=wl_stop, wl_step=wl_step, additional_filter=None)
print('Done.')


def dump_kappa(poly):
    integrated_old = [0 for i in range(5)]
    integrated_new = [0 for i in range(5)]
    integrated_rel = [0 for i in range(5)]
    for wl_ind in range(len(wl_arr) - 1):
        for ch in range(5):
            integrated_old[ch] += (kappa_old.rel_sens(poly, ch + 1, wl_arr[wl_ind]) + kappa_old.rel_sens(poly, ch + 1,
                                                                                                         wl_arr[
                wl_ind + 1])) * 0.5 * (wl_arr[wl_ind + 1] - wl_arr[wl_ind])
            integrated_new[ch] += (kappa_new.rel_sens(poly, ch + 1, wl_arr[wl_ind]) + kappa_new.rel_sens(poly, ch + 1,
                                                                                                         wl_arr[
                                                                                                             wl_ind + 1])) * 0.5 * (
                                              wl_arr[wl_ind + 1] - wl_arr[wl_ind])
    print('Poly %d' % poly)
    print(integrated_old)
    print(integrated_old)
    line = ''
    for ch in range(5):
        line += '%.2f ' % (integrated_new[ch]/integrated_old[ch])
    print('%s\n' % line)


for poly in range(10):
    dump_kappa(poly)


