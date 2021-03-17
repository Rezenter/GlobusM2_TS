import ijson
import math
import statistics

#shots = [382, 383, 384, 386, 387] #base = 384
shots = [384]
ophir_path = 'd:/data/db/calibration/energy/'
caen_path = 'd:/data/db/debug/raw/'



adc_gr = 0
adc_ch = 0
trigger_threshold = 200
offset = 1100

time_step = 1 / 3.2
prehistory_separator = 10
adc_baseline = 1250
offscale_threshold = 50
laser_prehistory_residual_pc = 20 / 100
laser_integral_residual_pc = 1 / 100
laser_length_residual_ind = 5
left_limit = 100  # ind
right_limit = 20  # ind

ophir_skip_lines = 38

shape_length = 200

shape = [
    1.0005554812368231,
    1.5248643888819124,
    2.417793378837268,
    3.876206116002449,
    6.488710824428781,
    10.901241167620753,
    18.542318176549326,
    30.47986421449577,
    47.78786644663863,
    71.3651373032234,
    100.3871457086363,
    133.45317563330147,
    168.2976448018283,
    202.5314211341387,
    234.85490711349132,
    264.30668585233053,
    290.68112206187294,
    313.9996296651095,
    334.413149126605,
    352.5115160002099,
    368.8490948227545,
    383.77232811656023,
    397.7858205482009,
    411.173097159529,
    424.31423642431696,
    437.2907061508794,
    450.09455816678343,
    462.8252834388258,
    475.43902646337943,
    487.82800264223,
    500.1751563113147,
    511.93680234228566,
    523.0718736662254,
    533.3299081598079,
    542.3149036257678,
    550.1525743498191,
    556.7038592270513,
    561.7926676464152,
    565.9059731360916,
    568.4975671999866,
    569.9037805788928,
    570.1639819949085,
    569.2505540861473,
    567.3187354128772,
    564.2981170395514,
    560.3403718526095,
    555.5922472013816,
    550.0951564857008,
    543.7983624008795,
    537.0484891796183,
    529.7883536815713,
    522.1422383076874,
    514.1178659234798,
    505.77505586488616,
    497.3675056416719,
    488.6311665303438,
    479.82069324630356,
    471.0050963224754,
    462.1568701785021,
    453.3137556416718,
    444.5135531793393,
    435.73461152894856,
    427.1329567786696,
    418.58150989669423,
    410.22299932889285,
    402.0869369684017,
    393.95796985763167,
    386.13268456187274,
    378.40792765618085,
    370.8477473408907,
    363.5197118009911,
    356.2320295674532,
    349.0681869684019,
    342.14250529289967,
    335.5000096525537,
    328.9362298325202,
    322.4838763168952,
    315.986840532855,
    309.71011445863627,
    303.4898267214711,
    297.27460542543315,
    291.25760033335735,
    285.13120140757604,
    279.2051207365381,
    273.31083554541095,
    267.36435866901587,
    261.5932089410582,
    255.84815575327923,
    250.10889863832384,
    244.52702381271,
    239.04925595556722,
    233.5552323436811,
    228.24563709396017,
    222.86286156382624,
    217.7309152398865,
    212.7342974594735,
    207.6958976268842,
    202.77980806215209,
    197.85885172844678,
    193.16920102392655,
    188.50767758642655,
    183.9181995242056,
    179.67192999295557,
    175.35126802308946,
    171.02738095556714,
    166.87664208140419,
    162.7753038420069,
    158.7629201575761,
    154.83503929820105,
    150.8009553487033,
    147.186934875768,
    143.52216628620326,
    139.93780732973008,
    136.2742936229778,
    132.75268613134838,
    129.3465719781676,
    126.07856590952922,
    122.71463437353593,
    119.57849911962964,
    116.45233892850239,
    113.32174270221891,
    110.25991757666083,
    107.34525047984168,
    104.60971807889301,
    101.72833798681712,
    98.8181187834131,
    96.28462635177247,
    93.70434768268764,
    91.03285458837964,
    88.55595656940642,
    86.13733090673901,
    83.62197603090195,
    81.2334443623752,
    78.90166998318992,
    76.68939267431715,
    74.47257626806716,
    72.28057710512073,
    70.07750354903814,
    68.03737868854707,
    66.06234241622563,
    64.10626994133725,
    62.05657232693991,
    60.118712393904204,
    58.28171636990867,
    56.369408543457766,
    54.63312854903813,
    52.92206357275465,
    51.155508745745735,
    49.42112554959619,
    47.71473168101363,
    46.191092590611845,
    44.63504522733059,
    43.03710158893774,
    41.531155544015874,
    40.00169526918328,
    38.59249936377032,
    37.17209095138194,
    35.640176365723455,
    34.405908090053806,
    33.1096368149422,
    31.74836344719667,
    30.52645705768773,
    29.294524161482375,
    27.975765442174342,
    26.83679955210736,
    25.617576093681027,
    24.5794027887145,
    23.45045154708503,
    22.248637582241283,
    21.203402858468962,
    20.138733669015842,
    19.140711556850665,
    18.174780334752448,
    17.003462324149773,
    16.04615031243102,
    15.140520080846205,
    14.20243274825692,
    13.374494341448884,
    12.444033264439955,
    11.520080104562718,
    10.720308724819416,
    9.819231715890842,
    9.135200431013608,
    8.252310852330572,
    7.394916181571638,
    6.640700570522531,
    5.842401009975659,
    5.105554609306018,
    4.372483669015841,
    3.6614969921185216,
    2.9926250961921803,
    2.2767005007680714,
    1.5353723757680726,
    0.9337237290046803,
    0.2476882239823595,
    -0.32172723360692623,
    -0.993337515414963,
    -1.6557642732274638,
    -2.1820526381828214,
    -2.7691911356716594
]


def find_front_index(signal, threshold, rising=True):
    if rising:
        for i in range(len(signal) - 1):
            if signal[i + 1] >= threshold > signal[i]:
                return i + (threshold - signal[i]) / (signal[i + 1] - signal[i])
    else:
        for i in range(len(signal) - 1):
            if signal[i] >= threshold > signal[i + 1]:
                return i + (signal[i] - threshold) / (signal[i] - signal[i + 1])
    return -1


def integrate_energy(signal, zero):
    res = 0.0
    flag = False
    for i in range(len(signal) - 1):
        if signal[i] - zero >= trigger_threshold:
            flag = True
        res += time_step * (signal[i] + signal[i + 1] - 2 * zero) * 0.5  # ns*mV

        if flag and signal[i + 1] - zero < 0:
            break
    else:
        print('Warning! Energy integration failed to stop.')
        exit()
    if event_ind > 1e5:
        for i in range(len(signal) - 1):
            print(signal[i] - zero)
        fuck
    return res


def pullOn(signal, zero):
    top = 0
    bot = 0
    for cell_ind in range(shape_length):
        top += (signal[cell_ind] - zero) * shape[cell_ind]
        bot += math.pow(shape[cell_ind], 2)
    return top / bot


for shotn in shots:
    ophir = []
    with open('%s%d.txt' % (ophir_path, shotn), 'r') as ophir_fp:
        for line_ind in range(ophir_skip_lines):
            ophir_fp.readline()
        for line in ophir_fp:
            ophir.append(float(line.split()[1]))

    caen = []
    averaging = []
    print('Loading raw...')
    with open('%s/%05d/0.json' % (caen_path, shotn), 'rb') as board_file:
        for event in ijson.items(board_file, 'item', use_float=True):
            caen.append(event['groups'])
    print('raw loaded')

    if len(ophir) != len(caen):
        print(len(ophir), len(caen))
        print('\n\n\nWARNING!!! pulse count does not match\n\n\n')
        # fuck

    caen_laser = []
    for event_ind in range(len(caen)):
        if 'captured_bad' in caen[event_ind] and \
                caen[event_ind]['captured_bad']:
            fuck

        signal = caen[event_ind][adc_gr]['data'][adc_ch]
        front_ind = find_front_index(signal, trigger_threshold)
        integration_limit = math.floor(front_ind) - prehistory_separator
        if integration_limit < left_limit:
            error = 'Sync left'
            fuck
        zero = statistics.fmean(signal[:integration_limit])
        maximum = float('-inf')
        minimum = float('inf')
        for cell in signal:
            maximum = max(maximum, cell)
            minimum = min(minimum, cell)
        if minimum - offscale_threshold < offset - adc_baseline or \
                maximum + offscale_threshold > offset+ adc_baseline:
            error = 'sync offscale'
            fuck
        integral = integrate_energy(signal[integration_limit:], zero)

        averaging.append([])
        for cell in range(integration_limit, integration_limit + shape_length):
            averaging[-1].append(signal[cell] - zero)

        caen_laser.append({
            'pre_std': statistics.stdev(signal[:integration_limit], zero),
            'int': integral,
            'pull': pullOn(signal[integration_limit:], zero)
        })

    if len(ophir) != len(caen_laser):
        print('\n\n\nWARNING!!! pulse count does not match\n\n\n')
        #fuck


    for index in range(shape_length):
        val = 0
        for shot in averaging:
            val += shot[index]
        val /= len(averaging)
        print(val)

    with open('%d.csv' % shotn, 'w') as out_fp:
        for ind in range(len(caen_laser)):
            out_fp.write('%.4f, %.2f, %.4f\n' % (ophir[ind], caen_laser[ind]['int'], caen_laser[ind]['pull']))


print('OK')