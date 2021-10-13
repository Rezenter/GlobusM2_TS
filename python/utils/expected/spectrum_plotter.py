import sp_dens

wl_start = 400
wl_stop = 1350
wl_step = 1

#lambda0 = 1064
#lambda0 = 946
#lambda0 = 532
lambda0 = 1320

theta_deg = 170
#theta_deg = 115

temperatures = [100, 500, 1e3, 5e3, 10e3, 20e3, 30e3]

wl_arr = []
current_wl = wl_start
while current_wl <= wl_stop:
    wl_arr.append(current_wl)
    current_wl += wl_step

print(lambda0, theta_deg, '\n')

cross = sp_dens.Selden(4, '2020.11.20', lambda0, theta_deg)
for wl in wl_arr:
    res = '%.2f ' % wl
    for T in temperatures:
        res += '%.3f %.3f ' % (cross.scat_power_dens(T, wl) * 2e3, sp_dens.Naito(T, wl, theta_deg, lambda0))
    print(res[:-1])



