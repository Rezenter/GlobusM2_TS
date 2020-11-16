import rawToSignals
import checkConfig

DB_PATH = 'd:/data/GTS-Core-2020/db/'
PLASMA_SHOTS = 'plasma/'
DEBUG_SHOTS = 'debug/'
RAW_FOLDER = 'raw/'
HEADER_FILE = 'header'
FILE_EXT = 'json'

config = '2020.11.12'
#if not checkConfig.check(config):
#    print('Config is not valid!')
#    exit(-1)

integrator = rawToSignals.Integrator(DB_PATH, 294, True, '2020.11.12')

#integrator.process_shot()

#for poly in range(10):
#    integrator.plot(416, poly)

print('manual processing finished')
