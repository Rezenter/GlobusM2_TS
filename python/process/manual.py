import rawToSignals
import checkConfig

config = '2020.11.12'
if not checkConfig.check(config):
    print('Config is not valid!')
    exit(-1)

# use timestamps instead!
missing_events = [
    [78],
    [],
    [],
    []
]  # add missing event_ind for corresponding board.

integrator = rawToSignals.Integrator(294, True, config, missing_events)
if not integrator.loaded:
    print('Loading sailed!')
    exit(-2)

integrator.process_shot()

integrator.plot(427, 0)

print('manual processing finished')
