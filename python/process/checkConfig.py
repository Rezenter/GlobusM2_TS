import ijson

# check int_from < int_to
# check gain values

extension = '.json'
config_path = '../configs/'
board_count = 4
board_ch_count = 16
poly_count = 10
spectral_ch_count = 6
crate = [
    [
        False for ch in range(board_ch_count)
    ] for board in range(board_count)
]
polys = [
    [
        False for ch in range(spectral_ch_count)
    ] for poly in range(poly_count)
]


def check(filename):
    config = {}
    bad = False
    with open('%s%s%s' % (config_path, filename, extension), 'r') as config_file:
        obj = ijson.kvitems(config_file, '')
        for k, v in obj:
            config[k] = v

    for board_ind in range(board_count):
        ch = config['adc']['sync'][board_ind]['ch']
        if crate[board_ind][ch]:
            print('ADC channel %d for board %d duplication.' % (ch, board_ind))
            bad = True
        crate[board_ind][ch] = True

    for poly_ind in range(poly_count):
        poly = config['poly'][poly_ind]
        for ch_ind in range(spectral_ch_count):
            ch = poly['channels'][ch_ind]
            if polys[poly['ind']][ch_ind]:
                print('Spectral channel %d for poly %d duplication.' % (ch_ind, poly['ind']))
                bad = True
            polys[poly['ind']][ch_ind] = True
            if crate[ch['adc']][ch['ch']]:
                print('ADC channel %d for board %d duplication.' % (ch['ch'], ch['adc']))
                bad = True
            crate[ch['adc']][ch['ch']] = True

    for poly_ind in range(poly_count):
        poly = polys[poly_ind]
        for ch_ind in range(spectral_ch_count):
            if not poly[ch_ind]:
                print('Spectral channel %d for poly %d is not covered by config.' % (ch_ind, poly_ind))
                bad = True
    for board_ind in range(board_count):
        board = crate[board_ind]
        for ch_ind in range(board_ch_count):
            if not board[ch_ind]:
                print('ADC channel %d for board %d is not covered by config.' % (ch_ind, board_ind))
                bad = True
    return not bad
