import phys_const
import json
import math

shotn: int = 44043
time_PET: float = 180
upscale: int = 50


z_eps: float = 0.00001
r_eps: float = 0.00008
flux_eps: float = 0.00003
r: list[float] = []
z: list[float] = []
flux: list[list[float]] = []

with open('in/%d_%s_eq_res.txt' % (shotn, str(round((time_PET / 1e3), 3))), 'r') as file:
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

axis_flux: float = -1e100
axis_r_ind: int = 0
axis_z_ind: int = 0
for r_ind in range(len(r)):
    for z_ind in range(len(z)):
        if axis_flux < flux[z_ind][r_ind]:
            axis_flux = flux[z_ind][r_ind]
            axis_r_ind = r_ind
            axis_z_ind = z_ind
for index_1 in range(len(flux_up)):
    for index_2 in range(len(flux_up[0])):
        top: float = phys_const.interpolate(x_prev=0, x_next=upscale, x_tgt=index_2 % upscale, y_prev=flux[index_1 // upscale][index_2 // upscale], y_next=flux[index_1 // upscale][1 + index_2 // upscale])
        bot: float = phys_const.interpolate(x_prev=0, x_next=upscale, x_tgt=index_2 % upscale, y_prev=flux[index_1 // upscale + 1][index_2 // upscale], y_next=flux[index_1 // upscale + 1][1 + index_2 // upscale])
        flux_up[index_1][index_2] = phys_const.interpolate(x_prev=0, x_next=upscale, x_tgt=index_1 % upscale, y_prev=top, y_next=bot)

print(axis_flux, r[axis_r_ind], z[axis_z_ind])

def find_surface(target_R: float, target_Z: float = 0):
    tgt_flux: float = 0
    for index_1 in range(len(flux_up)):
        if target_Z-z_eps <= z_up[index_1] <= target_Z+z_eps:
            for index_2 in range(len(flux_up[0])):
                if target_R-r_eps <= r_up[index_2] <= target_R+r_eps:
                    tgt_flux = flux_up[index_1][index_2]
                    #print(z_up[index_1], r_up[index_2], tgt_flux)

    res: list = []
    for index_1 in range(len(flux_up)):
        for index_2 in range(len(flux_up[0])):
            if tgt_flux - flux_eps <= flux_up[index_1][index_2] <= tgt_flux + flux_eps:
                res.append((r_up[index_2], z_up[index_1]))
    return {
        'points': res,
        'flux': tgt_flux
    }

lcfs = []
lcfm_lfs_r: float = 0.605
lcfs_found: bool = False
while not lcfs_found:
    print('try Rlcfs=', lcfm_lfs_r)
    lcfs = find_surface(target_R=lcfm_lfs_r, target_Z=z[axis_z_ind])


    #if limiter:
    limiter_hfs = 0.125
    limiter_lfs = 0.61
    for point in lcfs['points']:
        if not limiter_hfs < point[0] < limiter_lfs:
            lcfs_found = True
            print('limiter configuration: ', point[0], point[1])
            break

    #if divertor

    lcfm_lfs_r += 0.0001

out = lcfs#find_surface(target_R=0.5)

ts_data = None
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%s\\result.json' % shotn, 'r') as file:
    ts_data = json.load(file)
    for poly in ts_data['config']['poly']:
        surf = find_surface(target_R=poly['R']*1e-3)
        rho = math.sqrt((surf['flux'] - lcfs['flux'])/(axis_flux-lcfs['flux']))
        print(poly['R'], surf['flux'], rho)

print(axis_flux, lcfs['flux'])

with open('surface.csv', 'w') as file:
    for point in out['points']:
        file.write('%.7f, %.7f\n' %(point[0], point[1]))

print('code OK')
