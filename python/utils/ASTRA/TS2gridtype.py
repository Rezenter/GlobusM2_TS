R = '''602
592
571
545
522
497
475
451
429
409
289'''

te = '''35,85191
115,18694
299,03016
599,61328
841,7627
1265,2476
1348,24976
1390,07283
1427,4503
1432,92743
977,51983'''

ne = '''8,33E+18
1,56E+19
2,55E+19
3,90E+19
5,18E+19
6,28E+19
6,99E+19
7,42E+19
8,01E+19
8,13E+19
5,06E+19'''

'''
R_a = ['0.605']
te_a = ['0.05 ']
ne_a = ['0.5  ']
'''

R_a = []
te_a = []
ne_a = []

R = R.replace(',', '.')
te = te.replace(',', '.')
ne = ne.replace(',', '.')

R_a.extend(['%.3f'%(float(v)*1e-3) for v in R.split('\n')])
te_a.extend(['%.3f'%(float(v)*1e-3) for v in te.split('\n')])
ne_a.extend(['%.3f'%(float(v)*1e-19) for v in ne.split('\n')])

print('!*************** Te **********************************')
print('NAMEXP TEX POINTS %d GRIDTYPE 19' % (len(R_a)))
print(0.0)
print('        '.join(R_a))
print('        '.join(te_a))

print('\n\n!*************** ne **********************************')
print('NAMEXP NEX POINTS %d GRIDTYPE 19' % (len(R_a)))
print(0.0)
print('        '.join(R_a))
print('        '.join(ne_a))

print('\n\nOK')
