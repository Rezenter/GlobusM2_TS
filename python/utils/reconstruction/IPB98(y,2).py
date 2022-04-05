C_tau = 0.0562  # 1, numerical coeff for confinement time
C_w = 9.3  # 1, numerical coeff for stored energy
R = 0.36  # m, geometry center R
epsilon = 0.24 / 0.36  # 1, inverse aspect ratio

'''
# Globus-M2 41105, 195ms
I_p = 0.41  # MA, plasma current
B_tor = 0.8  # T, toroidal magnetic field on axis
U_plasma = 0.80  # V, plasma voltage
P_NBI = 0.75  # MW, output NBI power
NBI_eff = 0.65  # 1, NBI power absorption efficiency
n_e = 7.41  # m^-3 e 19, line average density
W_experimental = 9.248  # kJ, measured stored energy, Diamagnetic data from N.V.
M = 2  # AMU, average ion mass (without impurity)
k = 1.8  # 1, elongation
'''

'''
# Globus-M2 41105, 195ms
I_p = 0.41  # MA, plasma current
B_tor = 0.8  # T, toroidal magnetic field on axis
U_plasma = 0.80  # V, plasma loop voltage
P_NBI = 0.75  # MW, output NBI power
NBI_eff = 0.65  # 1, NBI power absorption efficiency
n_e = 7.41  # m^-3 e 19, line average density
W_experimental = 11.6  # kJ, modelled stored energy, value from Ann`s modelling
M = 2  # AMU, average ion mass (without impurity)
k = 1.8  # 1, elongation
'''
'''
# Globus-M2 41226, 180ms
I_p = 0.41  # MA, plasma current
B_tor = 0.8  # T, toroidal magnetic field on axis
U_plasma = 1.40  # V, plasma loop voltage
P_NBI = 0.75  # MW, output NBI power
NBI_eff = 0.65  # 1, NBI power absorption efficiency
n_e = 10.3  # m^-3 e 19, line average density
W_experimental = 11.165  # kJ, measured stored energy, Diamagnetic data from N.V.
M = 2  # AMU, average ion mass (without impurity)
k = 1.68  # 1, elongation
'''
'''
# Globus-M2 40975, 201ms
I_p = 0.25  # MA, plasma current
B_tor = 0.7  # T, toroidal magnetic field on axis
U_plasma = 1.0  # V, plasma loop voltage
P_NBI = 0.55  # MW, output NBI power      !!!!!!!!!!!!!!!!!!!!!!!!
fuckUp
NBI_eff = 0.65  # 1, NBI power absorption efficiency
n_e = 7.3  # m^-3 e 19, line average density
W_experimental = 4 * (9.05/6.8)  # kJ, measured stored energy, from TS W_e
M = 2  # AMU, average ion mass (without impurity)
k = 1.7  # 1, elongation
'''
# Globus-M2 41114, 201ms
I_p = 0.4  # MA, plasma current
B_tor = 0.8  # T, toroidal magnetic field on axis
U_plasma = 1.0  # V, plasma loop voltage # 1.1
P_NBI = 0.75  # MW, output NBI power      !!!!!!!!!!!!!!!!!!!!!!!!
NBI_eff = 0.6  # 1, NBI power absorption efficiency
n_e = 7.2  # m^-3 e 19, line average density
W_experimental = 9.2  # kJ, measured total stored energy
M = 3  # AMU, average ion mass (without impurity)
k = 1.7  # 1, elongation

P_absorbed = P_NBI * NBI_eff + I_p * U_plasma  # MW, total absorbed power = absorbed NBI + ohmic
W_IBP = C_w * pow(I_p, 0.93) * pow(B_tor, 0.15) * pow(P_absorbed, 0.31) * pow(n_e, 0.41)  # kJ, stored energy

print('OH power = %.2f MW' % (I_p * U_plasma))
print('NBI power = %.2f MW' % (P_NBI * NBI_eff))
print('total power = %.2f MW' % P_absorbed)
print('stored energy IBP = %.2f kJ' % W_IBP)

W_H_factor = W_experimental / W_IBP
print('W H-factor = %.2f\n' % W_H_factor)

tau_e_experimental = W_experimental / P_absorbed  # ms
print('experimental confinement time = %.2f ms' % tau_e_experimental)

tau_e_IBP = 1000 * C_tau * pow(I_p, 0.93) * pow(B_tor, 0.15) * pow(P_absorbed, -0.69) * pow(n_e, 0.41) * pow(M, 0.19) * \
            pow(R, 1.97) * pow(epsilon, 0.58) * pow(k, 0.78)  # ms, energy confinement time
print('IPB energy confinement time = %.2f ms' % tau_e_IBP)

tau_e_Glob = 1000 * 0.01 * pow(I_p, 0.43) * pow(B_tor, 1.19) * pow(P_absorbed, -0.59) * pow(n_e, 0.58)  # ms, energy confinement time
print('Glob energy confinement time = %.2f ms' % tau_e_Glob)

tau_H_factor = tau_e_experimental / tau_e_IBP
print('Tau_e H-factor = %.2f' % tau_H_factor)
