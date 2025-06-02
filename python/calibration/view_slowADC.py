import struct

chMap = [0, 2, 4, 6, 10, 8, 14, 12, 1, 3, 5, 7, 11, 9, 15, 13]

fiber = '3_fixed'
repeat = 19

with open('slow\\%s\\sht%05d\\192.168.10.51.slow' % (fiber, repeat), 'rb') as file:
    data_raw = file.read()
    point_count = int(len(data_raw) / (16 * 2))  # ch count = 16, sizeof(short) = 2
    # print(point_count, len(data))
    board = [[] for ch in range(16)]
    for ch_ind in range(16):
        for i in range(1, point_count):  # skip first as it is sometimes corrupted
            board[ch_ind].append(
                struct.unpack_from('<h', buffer=data_raw, offset=16 * i * 2 + 2 * chMap[ch_ind])[0])
    for v in board[3]:
        print(v)
