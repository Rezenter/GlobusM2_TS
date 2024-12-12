import json
import math
import phys_const
import copy
from pathlib import Path

shotn = 43498
surf_filename: str = 'g043498.000165'
lcfm_lfs_r: float = 0.5772  #0.5668999999999998
Rinv: float = 52.9

upscale: int = 100

flux_eps: float = 0.000003
r: list[float] = []
z: list[float] = []
flux: list[list[float]] = []

limiter_hfs = 0.125
limiter_lfs = 0.61
limiter_top = 0.49
limiter_bot = -limiter_top

class Equilibrium:
    def __init__(self, filename: str) -> None:
        self.error: str = ''
        self.__res: dict = {
            'filename': filename
        }

        if self.__read():
            self.__base_calc()

        with open('out/%s.json' % filename, 'w') as file:
            json.dump(self.__res, file)

    def __read(self) -> bool:
        path = Path('in/' + self.__res['filename'])
        if not path.is_file():
            self.error = 'Surface file %s not found!' % path
            print(self.error)
            return False

        with open(path, 'r') as file:
            curr = file.readline().split()
            self.__res['g_file']: dict = {
                'z_grid': int(curr[-1]),  # Number of horizontal R grid points
                'r_grid': int(curr[-2]),  # Number of vertical Z grid points
                'idum': int(curr[-3]),
                'name': ' '.join(curr[:-3]).rstrip('\x00')
            }

            curr_line = file.readline()
            curr = [curr_line[num * 16: (num + 1) * 16] for num in range(5)]
            self.__res['g_file'].update({
                'r_dim': float(curr[0]),  # Horizontal dimension in meter of computational box
                'z_dim': float(curr[1]),  # Vertical dimension in meter of computational box
                'r_centr': float(curr[2]),  # R in meter of vacuum toroidal magnetic field B_CENTR
                'r_left': float(curr[3]),  # Minimum R in meter of rectangular computational box
                'z_mid': float(curr[4])  # Z of center of computational box in meter
            })

            curr_line = file.readline()
            curr = [curr_line[num * 16: (num + 1) * 16] for num in range(5)]
            self.__res['g_file'].update({
                'r_m_axis': float(curr[0]),  # R of magnetic axis in meter
                'z_m_axis': float(curr[1]),  # Z of magnetic axis in meter
                'si_mag': float(curr[2]),  # poloidal flux at magnetic axis in Weber /rad
                'si_bry': float(curr[3]),  # poloidal flux at the plasma boundary in Weber /rad
                'b_centr': float(curr[4])  # Vacuum toroidal magnetic field in Tesla at RCENTR
            })

            curr_line = file.readline()
            curr = [curr_line[num * 16: (num + 1) * 16] for num in range(1)]
            self.__res['g_file'].update({
                'current': float(curr[0])  # Plasma current in Ampere
            })

            file.readline()

            self.__res['g_file']['f_pol'] = []  # Poloidal current function in m-T, F = RBT on flux grid
            while len(self.__res['g_file']['f_pol']) != self.__res['g_file']['r_grid']:
                curr_line = file.readline()
                size = 5
                if self.__res['g_file']['r_grid'] - len(self.__res['g_file']['f_pol']) < 5:
                    size = self.__res['g_file']['r_grid'] - len(self.__res['g_file']['f_pol'])
                buffer = [curr_line[num * 16: (num + 1) * 16] for num in range(size)]
                for val in buffer:
                    self.__res['g_file']['f_pol'].append(float(val))

            self.__res['g_file']['pres'] = []  # Plasma pressure in nt / m2 on uniform flux grid
            while len(self.__res['g_file']['pres']) != self.__res['g_file']['r_grid']:
                curr_line = file.readline()
                size = 5
                if self.__res['g_file']['r_grid'] - len(self.__res['g_file']['pres']) < 5:
                    size = self.__res['g_file']['r_grid'] - len(self.__res['g_file']['pres'])
                buffer = [curr_line[num * 16: (num + 1) * 16] for num in range(size)]
                for val in buffer:
                    self.__res['g_file']['pres'].append(float(val))

            self.__res['g_file']['ffprim'] = []  # FF’(y) in (mT)2 / (Weber /rad) on uniform flux grid
            while len(self.__res['g_file']['ffprim']) != self.__res['g_file']['r_grid']:
                curr_line = file.readline()
                size = 5
                if self.__res['g_file']['r_grid'] - len(self.__res['g_file']['ffprim']) < 5:
                    size = self.__res['g_file']['r_grid'] - len(self.__res['g_file']['ffprim'])
                buffer = [curr_line[num * 16: (num + 1) * 16] for num in range(size)]
                for val in buffer:
                    self.__res['g_file']['ffprim'].append(float(val))

            self.__res['g_file']['pprime'] = []  # P’(y) in (nt /m2) / (Weber /rad) on uniform flux grid
            while len(self.__res['g_file']['pprime']) != self.__res['g_file']['r_grid']:
                curr_line = file.readline()
                size = 5
                if self.__res['g_file']['r_grid'] - len(self.__res['g_file']['pprime']) < 5:
                    size = self.__res['g_file']['r_grid'] - len(self.__res['g_file']['pprime'])
                buffer = [curr_line[num * 16: (num + 1) * 16] for num in range(size)]
                for val in buffer:
                    self.__res['g_file']['pprime'].append(float(val))

            self.__res['g_file']['psi_rz'] = [[]]  # Poloidal flux in Weber / rad on the rectangular grid points
            self.__res['g_file']['si_min'] = float('inf')  # minimum poloidal flux in Weber /rad
            while len(self.__res['g_file']['psi_rz']) != self.__res['g_file']['z_grid'] or \
                    len(self.__res['g_file']['psi_rz'][-1]) != self.__res['g_file']['r_grid']:
                curr_line = file.readline()
                size = 5
                if len(self.__res['g_file']['psi_rz']) == self.__res['g_file']['z_grid'] and \
                        self.__res['g_file']['r_grid'] - len(self.__res['g_file']['psi_rz'][-1]) < 5:
                    size = self.__res['g_file']['r_grid'] - len(self.__res['g_file']['psi_rz'][-1])
                buffer = [curr_line[num * 16: (num + 1) * 16] for num in range(size)]
                for val in buffer:
                    self.__res['g_file']['psi_rz'][-1].append(float(val))
                    self.__res['g_file']['si_min'] = min(self.__res['g_file']['si_min'], float(val))
                    if len(self.__res['g_file']['psi_rz'][-1]) == self.__res['g_file']['r_grid'] and \
                            len(self.__res['g_file']['psi_rz']) != self.__res['g_file']['z_grid']:
                        self.__res['g_file']['psi_rz'].append([])

            self.__res['g_file']['q_psi'] = []  # q values on uniform flux grid from axis to boundary
            while len(self.__res['g_file']['q_psi']) != self.__res['g_file']['r_grid']:
                curr_line = file.readline()
                size = 5
                if self.__res['g_file']['r_grid'] - len(self.__res['g_file']['q_psi']) < 5:
                    size = self.__res['g_file']['r_grid'] - len(self.__res['g_file']['q_psi'])
                buffer = [curr_line[num * 16: (num + 1) * 16] for num in range(size)]
                for val in buffer:
                    self.__res['g_file']['q_psi'].append(float(val))

            curr = file.readline().split()
            self.__res['g_file'].update({
                'n_bbbs': int(curr[0]),  # Number of boundary points
                'limitr': int(curr[1])  # Number of limiter points
            })

            self.__res['g_file']['boundary'] = []  # boundary points
            buffer = []
            while len(self.__res['g_file']['boundary']) != self.__res['g_file']['n_bbbs']:
                curr_line = file.readline()
                size = 5
                if 2 * (self.__res['g_file']['n_bbbs'] - len(self.__res['g_file']['boundary'])) < len(buffer) + 5:
                    size = (self.__res['g_file']['n_bbbs'] - len(self.__res['g_file']['boundary'])) * 2 - len(buffer)
                buffer.extend([curr_line[num * 16: (num + 1) * 16] for num in range(size)])
                for pair_i in range(math.floor(len(buffer) * 0.5)):
                    self.__res['g_file']['boundary'].append({
                        'r': float(buffer[pair_i * 2]),
                        'z': float(buffer[pair_i * 2 + 1])
                    })
                buffer = buffer[(pair_i + 1) * 2:]

            self.__res['g_file']['limiter'] = []  # limiter points
            buffer = []
            while len(self.__res['g_file']['limiter']) != self.__res['g_file']['limitr']:
                curr_line = file.readline()
                size = 5
                if 2 * (self.__res['g_file']['limitr'] - len(self.__res['g_file']['limiter'])) < len(buffer) + 5:
                    size = (self.__res['g_file']['limitr'] - len(self.__res['g_file']['limiter'])) * 2 - len(buffer)
                buffer.extend([curr_line[num * 16: (num + 1) * 16] for num in range(size)])
                for pair_i in range(math.floor(len(buffer) * 0.5)):
                    self.__res['g_file']['limiter'].append({
                        'r': float(buffer[pair_i * 2]),
                        'z': float(buffer[pair_i * 2 + 1])
                    })
                buffer = buffer[(pair_i + 1) * 2:]
        return True

    def r_at_ind(self, r_ind: float) -> float:
        return self.__res['g_file']['r_left'] + self.__res['g_file']['r_dim'] * r_ind / self.__res['g_file']['r_grid']

    def z_at_ind(self, z_ind: float) -> float:
        return self.__res['g_file']['z_mid'] + \
                self.__res['g_file']['z_dim'] * \
                (z_ind - self.__res['g_file']['z_grid'] * 0.5) / self.__res['g_file']['z_grid']

    def __base_calc(self) -> bool:
        global r, z, flux
        r = [(self.__res['g_file']['r_left'] + i * self.__res['g_file']['r_dim']/self.__res['g_file']['r_grid']) for i in range(self.__res['g_file']['r_grid'])]
        z = [(self.__res['g_file']['z_mid'] + (i - (self.__res['g_file']['z_grid'] - 1) / 2) * self.__res['g_file']['z_dim']/self.__res['g_file']['z_grid']) for i in range(self.__res['g_file']['z_grid'])]
        flux = self.__res['g_file']['psi_rz']

        while z[0] < limiter_bot - 0.01:
            z.pop(0)
            flux.pop(0)
        while z[-1] > limiter_top + 0.01:
            z.pop(-1)
            flux.pop(-1)

        while r[0] < limiter_hfs - 0.01:
            r.pop(0)
            for v in flux:
                v.pop(0)
        while r[-1] > limiter_lfs + 0.01:
            r.pop(-1)
            for v in flux:
                v.pop(-1)

        return True

    def flux_at(self, r: float, z: float) -> float:
        r_i: float = (r - self.__res['g_file']['r_left']) * self.__res['g_file']['r_grid'] / \
                     self.__res['g_file']['r_dim']
        z_i: float = (z - self.__res['g_file']['z_mid']) * self.__res['g_file']['z_grid'] / \
                     self.__res['g_file']['z_dim'] + self.__res['g_file']['z_grid'] * 0.5
        return self.__flux_at_ind(r_i, z_i)

    def __flux_at_ind(self, r_i: float, z_i: float) -> float:
        left: float = phys_const.interpolate(x_prev=math.floor(z_i), x_tgt=z_i, x_next=math.ceil(z_i),
                                             y_prev=self.__res['g_file']['psi_rz'][math.floor(z_i)][math.floor(r_i)],
                                             y_next=self.__res['g_file']['psi_rz'][math.ceil(z_i)][math.floor(r_i)])
        right: float = phys_const.interpolate(x_prev=math.floor(z_i), x_tgt=z_i, x_next=math.ceil(z_i),
                                              y_prev=self.__res['g_file']['psi_rz'][math.floor(z_i)][math.ceil(r_i)],
                                              y_next=self.__res['g_file']['psi_rz'][math.ceil(z_i)][math.ceil(r_i)])

        return phys_const.interpolate(x_prev=math.floor(r_i), x_tgt=r_i, x_next=math.ceil(r_i),
                                      y_prev=left, y_next=right)

    def get_ra(self, r: float, z: float) -> dict:
        target_flux: float = self.flux_at(r=r, z=z)

        if r >= self.__res['g_file']['r_m_axis']:
            # LFS
            step: int = 1
            a: float = self.__res['calc']['a']
        else:
            # HFS
            step: int = -1
            a: float = self.__res['calc']['-a']
        r_i: float = (self.__res['g_file']['r_m_axis'] - self.__res['g_file']['r_left']) * \
                     self.__res['g_file']['r_grid'] / self.__res['g_file']['r_dim']
        z_i: float = (self.__res['g_file']['z_m_axis'] - self.__res['g_file']['z_mid']) * \
                     self.__res['g_file']['z_grid'] / \
                     self.__res['g_file']['z_dim'] + self.__res['g_file']['z_grid'] * 0.5
        curr_flux: float = self.__flux_at_ind(r_i, z_i)
        if curr_flux <= target_flux:
            return {
                'ra': 0,
                'r': 0,
                'R': self.__res['g_file']['r_m_axis'],
                'flux': target_flux
            }
        prev_flux: float = curr_flux
        while curr_flux > target_flux:
            r_i += step
            prev_flux = curr_flux
            curr_flux = self.__flux_at_ind(r_i, z_i)
        final_r_i: float = phys_const.interpolate(x_prev=prev_flux, x_tgt=target_flux, x_next=curr_flux,
                                                  y_prev=r_i - step, y_next=r_i)
        final_r: float = self.r_at_ind(final_r_i) - self.__res['g_file']['r_m_axis']
        return {
            'ra': final_r / a,
            'r': final_r,
            'R': final_r + self.__res['g_file']['r_m_axis'],
            'flux': target_flux
        }

    def get_res(self) -> dict:
        if len(self.error) > 0:
            return {
                'error': self.error
            }
        return copy.deepcopy(self.__res)

result = {}
result['surfaces'] = []

eq_loader = Equilibrium(filename=surf_filename)
equilibrium = eq_loader.get_res()

r_up: list[float] = []
for real_ind in range(len(r) - 1):
    for fake_ind in range(upscale):
        r_up.append(r[real_ind] + (r[real_ind + 1] - r[real_ind]) * fake_ind / upscale)

z_up: list[float] = []
for real_ind in range(len(z) - 1):
    for fake_ind in range(upscale):
        z_up.append(z[real_ind] + (z[real_ind + 1] - z[real_ind]) * fake_ind / upscale)

flux_up: list[list[float]] = [[0] * (len(flux[0]) - 1) * upscale for i in range((len(flux) - 1) * upscale)]

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
        if z_up[index_1] <= target_Z <= z_up[index_1 + 1]:
            for index_2 in range(len(flux_up[0])):
                #print(target_R - r_eps, r_up[index_2], target_R + r_eps, 'R')
                if r_up[index_2] <= target_R <= r_up[index_2 + 1]:
                    #print(target_R-r_eps, r_up[index_2], target_R+r_eps, 'R')
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
lcfs_found: bool = False
while not lcfs_found:
    print('try Rlcfs=', lcfm_lfs_r)
    lcfs = find_surface(target_R=lcfm_lfs_r, target_Z=z[axis_z_ind])
    # if limiter:
    for point in lcfs['points']:
        if not limiter_hfs < point[0] < limiter_lfs:
            lcfs_found = True
            print('limiter configuration: ', point[0], point[1])
            break

    else:
        # if divertor

        proj: list[float] = []
        check: bool = False
        for point in lcfs['points']:
            if point[1] not in proj:
                proj.append(point[1])
                if not limiter_bot < point[1] < limiter_top:
                    check = True
        if check:
            proj.sort()
            for i in range(len(proj)):
                if proj[i] >= z[axis_z_ind]:
                    lcfs_found = True
                    print('divertor configuration')
                    print('Warning! lower null only!')
                    break
                if abs(proj[i + 1] - proj[i]) > abs(z_up[0] - z_up[1])*1.1:
                    #there is a gap between lower legs and lcfs
                    break

    lcfm_lfs_r += 0.0001

out = lcfs#find_surface(target_R=0.5)

surfaces = [lcfs['points']]

ts_data = None
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%s\\result.json' % shotn, 'r') as file:
    ts_data = json.load(file)

for poly in ts_data['config']['poly']:
    surf = find_surface(target_R=poly['R']*1e-3)
    rho = math.sqrt((surf['flux'] - axis_flux)/(lcfs['flux'] - axis_flux))
    print(poly['R'], surf['flux'], rho)
    surfaces.append(surf['points'])

i=0
for s in surfaces:
    with open('surface_%d.csv' % i, 'w') as file:
        for point in s:
            file.write('%.7f, %.7f\n' % (point[0], point[1]))
    i+=1



#surf = find_surface(target_R=Rinv)
#rho = math.sqrt((surf['flux'] - axis_flux)/(lcfs['flux'] - axis_flux))
#print('Rinv = ', Rinv, surf['flux'], rho)


print(axis_flux, lcfs['flux'])



print('code OK')

