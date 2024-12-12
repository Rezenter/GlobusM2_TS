points = {
    'T-11': {
        'R': 70,
        'a': 12.5,
        'q': 2.5,
        '<ne>': 1.5e13,
        '<Te>': 150
    }
}

for k in points:
    p = points[k]
    p['tau_ee_MM'] = 3.5e-21 * ((p['a'] / p['R'])**0.25) * p['q'] * p['<ne>'] * (p['R']**3) / (p['<Te>']**0.5)


    print(p['tau_ee_MM'] * 1e3)