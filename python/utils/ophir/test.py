import msgpack

with open('d:\\data\\db\\plasma\\ophir\\42834.msgpk', 'rb') as file:
    data = msgpack.unpackb(file.read())
    pass