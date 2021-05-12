import math


def get_surface(t_ind, ra=1, theta_step=(0.2 * math.pi / 180)):
    unused = t_ind
    r = []
    z = []
    theta = 0
    while theta < math.tau:
        #print(theta / math.tau, math.cos(theta), math.sin(theta))
        r.append(ra * math.cos(theta))
        z.append(ra * math.sin(theta))
        theta += theta_step
    return r, z
