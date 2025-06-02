import msgpack

shotn = 1003


path = 'd:\\data\\db\\debug\\raw\\%05d\\ophir.msgpk' % shotn
with open(path, 'rb') as file:
    ophir = msgpack.load(file)
    print('ophir', len(ophir))


for i in range(8):
    path = 'd:\\data\\db\\debug\\raw\\%05d\\%d.msgpk' % (shotn, i)
    with open(path, 'rb') as file:
        data = msgpack.load(file)
        print(i, len(data))

print(' ')
#for i in ophir:
#    print(i)

print('Code OK')
