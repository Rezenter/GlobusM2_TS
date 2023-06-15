import phys_const

shotn: int = 43220
time: float = 0.152
upscale: int = 50
target_R: float = 0.592

z_eps: float = 0.00001
r_eps: float = 0.0001
flux_eps: float = 0.00003
r: list[float] = []
z: list[float] = []
flux: list[list[float]] = []

with open('in/%d_%.3f_eq_res.txt' % (shotn, time), 'r') as file:
    z = [float(v) for v in file.readline().split()]
    for line in file:
        tmp = [float(v) for v in line.split()]
        r.append(tmp[0])
        flux.append(tmp[1:])

#upscale
r_up: list[float] = []
for real_ind in range(len(r) - 1):
    for fake_ind in range(upscale):
        r_up.append(r[real_ind] + (r[real_ind + 1] - r[real_ind]) * fake_ind / upscale)

z_up: list[float] = []
for real_ind in range(len(z) - 1):
    for fake_ind in range(upscale):
        z_up.append(z[real_ind] + (z[real_ind + 1] - z[real_ind]) * fake_ind / upscale)

flux_up: list[list[float]] = [[0] * (len(flux) - 1) * upscale for i in range((len(flux[0]) - 1) * upscale)]

tgt_flux: float = 0
for index_1 in range(len(flux_up)):
    for index_2 in range(len(flux_up[0])):
        top: float = phys_const.interpolate(x_prev=0, x_next=upscale, x_tgt=index_2 % upscale, y_prev=flux[index_1 // upscale][index_2 // upscale], y_next=flux[index_1 // upscale][1 + index_2 // upscale])
        bot: float = phys_const.interpolate(x_prev=0, x_next=upscale, x_tgt=index_2 % upscale, y_prev=flux[index_1 // upscale + 1][index_2 // upscale], y_next=flux[index_1 // upscale + 1][1 + index_2 // upscale])
        flux_up[index_1][index_2] = phys_const.interpolate(x_prev=0, x_next=upscale, x_tgt=index_1 % upscale, y_prev=top, y_next=bot)
        if -z_eps <= z_up[index_1] <= z_eps:
            if target_R-r_eps <= r_up[index_2] <= target_R+r_eps:
                tgt_flux = flux_up[index_1][index_2]
                print(z_up[index_1], r_up[index_2], tgt_flux)

out: list[str] = []
for index_1 in range(len(flux_up)):
    for index_2 in range(len(flux_up[0])):
        if tgt_flux - flux_eps <= flux_up[index_1][index_2] <= tgt_flux + flux_eps:
            out.append('%.7f, %.7f\n' % (r_up[index_2], z_up[index_1]))

with open('surface.csv', 'w') as file:
    file.writelines(out)

print('code OK')
