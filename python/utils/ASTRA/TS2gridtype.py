R = '''600
590
570
545
521
497
474
453
431
410'''

te = '''26.2
116.7
333.4
599.9
928.8
1120.8
1199.7
1230
1275
1294.5'''

ne = '''4.48E18
1.03E19
1.66E19
2.46E19
3.04E19
3.39E19
3.67E19
3.85E19
4.01E19
4.12E19'''

R_a = ['0.605']
te_a = ['0.05 ']
ne_a = ['0.5  ']

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
