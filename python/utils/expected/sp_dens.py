import phys_const as const
import json
import math
import scipy.special as sci

db_path = 'd:/data/db/'
FIBER_FOLDER = 'fibers/'


class Selden:
    def __init__(self, fiber_ind, config, lambda0=1064, theta_deg=None):
        self.lambda_0 = lambda0  # [nm], laser wavelength
        with open('%s%s%s.json' % (db_path, FIBER_FOLDER, config), 'r') as fiber_file:
            fibers = json.load(fiber_file)
            self.fiber = fibers[fiber_ind]
            if self.fiber['ind'] != fiber_ind:
                print('Error! Fiber index in config file is incorrect!')
                fuck
        self.alphaT = const.m_e * const.c * const.c / (2 * const.q_e)
        self.theta = self.fiber['theta'] * math.pi / 180.0
        if theta_deg is not None:
            self.theta = theta_deg * math.pi / 180.0

    def scat_power_dens(self, temp, wl):  # Scattering Power
        alpha = self.alphaT / temp
        x = (wl / self.lambda_0) - 1
        a_loc = math.pow(1 + x, 3) * math.sqrt(2 * (1 - math.cos(self.theta)) * (1 + x) + math.pow(x, 2))
        b_loc = math.sqrt(1 + x * x / (2 * (1 - math.cos(self.theta)) * (1 + x))) - 1
        c_loc = math.sqrt(alpha/math.pi)*(1 - (15/16)/alpha + 345/(512*alpha*alpha))
        return (c_loc / a_loc) * math.exp(-2 * alpha * b_loc) / self.lambda_0  # wtf i need /lambda_0?


def Naito(temp, wl, theta_deg, lambda0=1064):  # Scattering Power
    print('WARNING! 1/lambda0 may be required!')
    lambda_0 = lambda0  # [nm], laser wavelength
    theta = theta_deg * math.pi / 180.0
    j2ev = 6.241509e18

    alpha2 = const.m_e * math.pow(const.c, 2) * j2ev / temp
    epsilon = (wl - lambda_0) / lambda_0

    x = math.sqrt(
        1 + math.pow(epsilon, 2) / (2 * (1 - math.cos(theta)) * (1 + epsilon))
    )
    u = math.sin(theta) / (1 - math.cos(theta))
    y = math.pow(math.pow(x, 2) + math.pow(u, 2), -0.5)
    zeta = x * y
    eta = y / alpha2
    if sci.kn(2, alpha2) == 0 and math.exp(-alpha2 * x) == 0:
        return 0
    sz = math.exp(-alpha2 * x) / (sci.kn(2, alpha2) * math.pow(1 + epsilon, 3)) * math.pow(2 * (1 - math.cos(theta)) * (1 + epsilon) + math.pow(epsilon, 2), - 0.5)
    q = 1 - 4 * eta * zeta * (2 * zeta - (2 - 3 * math.pow(zeta, 2)) * eta) / (2 * zeta - (2 - 15 * math.pow(zeta, 2)) * eta)
    return sz * q

