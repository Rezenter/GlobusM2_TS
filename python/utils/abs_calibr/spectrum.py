import math
import phys_const as const

B0_vibr = 1.98973e2  # [1/m] rotational constant for the lowest vibrational level B0
Q_norm = 462.41585  # [1] rotational partition function (normalisation constant)
I_nucl = 1  # [1] nuclear spin
gamma_sq = 0.51e-60  # [m^6] square of polarizability tensor anisotropy

J_max = 40

db_path = 'd:/data/db/'
filter_path = 'filters/'
apd_path = 'apd/'
csv_ext = '.csv'

temperature = const.t_room  # [K] nitrogen in torus temperature
lambda_las = 1064e-9  # [m] laser wavelength

csv_header = 2
filters = {}


def get_g(j):  # [1] return statistical weight factor
    if j % 2:
        return 3
    return 6


def get_energy(j):  # [J] return rotational energy Ej
    return j * (j + 1) * const.h * const.c * B0_vibr


def get_fraction(j):  # [1] return fraction of molecules in the state J
    return (1 / Q_norm) * get_g(j) * (2 * j + 1) * math.exp(-get_energy(j) / (const.k_b * temperature))  # can be optimized


def get_normalisation_formula():  # [1] return normalisation coefficient calculated by approximate formula
    return math.pow(2 * I_nucl + 1, 2) * const.k_b * temperature / (2 * const.h * const.c * B0_vibr)


def wavelength2wavenumber(lambda_in):  # [1/m] return corresponding wavenumber
    return 1 / lambda_in


def wavenumber2wavelength(w_in):  # [m] return corresponding wavelength
    return 1 / w_in


def get_raman_shift(j):  # [1/m] return wavenumber shift
    return (4 * j - 2) * B0_vibr


def get_raman_wavelength(j):  # [m] return shifted wavelength for given laser and j
    return wavenumber2wavelength(
        wavelength2wavenumber(lambda_las) + get_raman_shift(j)
    )


def get_raman_section(j):  # [m^2 / sr] return differential cross-section
    first = 64 * math.pow(math.pi, 4) / 45
    sec = 3 * j * (j - 1) / (2 * (2 * j + 1) * (2 * j - 1))
    third = math.pow(wavelength2wavenumber(lambda_las) + get_raman_shift(j), 4)
    return first * sec * third * gamma_sq


def get_linearization(wl, array):
    for point_ind in range(len(array) - 1):
        curr = array[point_ind]
        next = array[point_ind + 1]
        if curr['wl'] <= wl < next['wl']:
            return (curr['v'] + (next['v'] - curr['v']) * (wl - curr['wl']) / (next['wl'] - curr['wl'])) * 0.01
    return 0


def get_qe():
    qe = []
    with open('%s%saw%s' % (db_path, apd_path, csv_ext), 'r') as aw_file:
        for i in range(csv_header):
            aw_file.readline()
        mult = const.h * const.c * 1e9 / const.q_e
        for line in aw_file:
            splitted = line.split(',')
            wl = float(splitted[0])
            r = float(splitted[1])
            qe.append({
                'wl': wl,
                'v': r * mult / wl
            })
    return qe


def load_filter(ch):
    ch_transmit = []
    with open('%s%sch%d%s' % (db_path, filter_path, ch, csv_ext), 'r') as filter_file:
        for i in range(csv_header):
            filter_file.readline()
        for line in filter_file:
            splitted = line.split(',')
            ch_transmit.append({
                'wl': float(splitted[0]),
                'v': float(splitted[1])
            })
    global filters
    ch_transmit.reverse()
    filters[ch] = ch_transmit


quant_exit = get_qe()
load_filter(1)
load_filter(2)


def get_sum(ch):
    summ = 0.0
    for j in range(2, J_max + 1):
        fj = get_fraction(j)
        wl = get_raman_wavelength(j)
        sigma = get_raman_section(j)
        summ += fj * sigma * (get_linearization(wl * 1e9, quant_exit) * get_linearization(wl * 1e9, filters[ch]))
    return summ


def check():
    summ = 0.0
    sig1 = 0.0
    sig2 = 0.0
    for j in range(2, J_max + 1):
        fj = get_fraction(j)
        #summ += fj
        wl = get_raman_wavelength(j)
        sigma = get_raman_section(j)
        res = fj * sigma
        #print('J = %2d, Fj = %.5f, sigma = %.5e, res = %.5e, wl = %.3f' % (j, fj, sigma, res, wl*1e9))
        qe = get_linearization(wl * 1e9, quant_exit)
        line1 = res * qe * get_linearization(wl * 1e9, filters[1])
        sig1 += line1
        line2 = res * qe * get_linearization(wl * 1e9, filters[2]) * (1 - get_linearization(wl * 1e9, filters[1]))
        sig2 += line2
        print('%.2f %.2e %.2f %.2e %.2e %.2e' % (wl*1e9, res, qe, res * qe, line1, line2))
        #print(sig1, sig2, sig1 / sig2)

    print(sig1, sig2, sig1/sig2)
    #print('formula = %.5f, summ = %.5f' % (get_normalisation_formula(), summ))
    "9.445147608304963e-36 8.776913057222178e-37 10.761354871269827"