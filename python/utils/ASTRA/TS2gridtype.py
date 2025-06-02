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

te = '''26.6
77
224.8
453.8
671.3
1044.1
1143
1170.2
1197.8
1236.1
940'''

ne = '''5.47E18
1.35E19
2.53E19
3.88E19
4.9E19
5.57E19
5.85E19
6.15E19
6.42E19
6.78E19
5.1E19'''

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
