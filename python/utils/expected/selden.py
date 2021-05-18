import phys_const as const
import json
import math

db_path = 'd:/data/db/'
FIBER_FOLDER = 'fibers/'


class Selden:
    def __init__(self, fiber_ind, config, lambda0=1064):
        self.lambda_0 = lambda0  # [nm], laser wavelength
        with open('%s%s%s.json' % (db_path, FIBER_FOLDER, config), 'r') as fiber_file:
            fibers = json.load(fiber_file)
            self.fiber = fibers[fiber_ind]
            if self.fiber['ind'] != fiber_ind:
                print('Error! Fiber index in config file is incorrect!')
                fuck
        self.alphaT = const.m_e * const.c * const.c / (2 * const.q_e)
        self.theta = self.fiber['theta'] * math.pi / 180.0

    def scat_power_dens(self, temp, wl):  # Scattering Power
        alpha = self.alphaT / temp
        x = (wl / self.lambda_0) - 1
        a_loc = math.pow(1 + x, 3) * math.sqrt(2 * (1 - math.cos(self.theta)) * (1 + x) + math.pow(x, 2))
        b_loc = math.sqrt(1 + x * x / (2 * (1 - math.cos(self.theta)) * (1 + x))) - 1
        c_loc = math.sqrt(alpha/math.pi)*(1 - (15/16)/alpha + 345/(512*alpha*alpha))
        return (c_loc / a_loc) * math.exp(-2 * alpha * b_loc) / self.lambda_0  # wtf i need /lambda_0?
