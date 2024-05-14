start = 0.41
stop = 0.60

count = 100
line = ''
for i in range(count):
    print('%.4f' % (start + (stop - start)*i/count))
print(stop)