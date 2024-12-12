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

te = '''22
96.2
304.6
620.9
978.2
1188.5
1220
1230
1256.5
1262.1'''

ne = '''4.53E18
1.17E19
2.08E19
3.14E19
4.16E19
4.61E19
4.9E19
5E19
5.23E19
5.43E19'''

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
