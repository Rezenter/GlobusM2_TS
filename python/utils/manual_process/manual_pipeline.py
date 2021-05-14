import integrator

shotn = 40105
is_plasma = True
config_name = '2021.05.12_g10'

LOCAL_DB_PATH = 'local_db/'
GLOBAL_DB_PATH = 'd:/data/db/'

raw_processor = integrator.Integrator(LOCAL_DB_PATH, shotn, is_plasma, config_name, GLOBAL_DB_PATH)

print('OK')
