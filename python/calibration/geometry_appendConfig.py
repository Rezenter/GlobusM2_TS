# read R from config_name.json, calculate scattering angle and append to the config_name.json

import json
import math
import phys_const  # at least v1.1

#DB_PATH: str = '\\\\172.16.12.130\\d\\data\\db\\config\\'
DB_PATH: str = 'd:\\data\\db\\config_cpp\\'

aperture_to_laser: float = 681.3  # mm. normal length from lens to the probing chord
center_to_laser: float = 169.6  # normal length from the tokamak center to the probing chord
normal_delta: float = 184.3  # distance between the normals

# change only this line!
#config_name: str = '2023.10.12'
#config_name: str = '2024.08.30_G2-10'
config_name: str = '2025.06.02'
# change only this line!

with open('%s%s.json' % (DB_PATH, config_name), 'r') as file:
    config = json.load(file)

for fiber_key in config['fibers']:
    fiber = config['fibers'][fiber_key]
    socket_ind: int = fiber['lens_socket_ind']
    if config['sockets'][socket_ind]['lens_socket'] != fiber['lens_socket']:
        print('Socket "%s" not found.' % fiber['lens_socket'])
        fuck
    fiber['lens_to_point']: float = math.sqrt(aperture_to_laser**2 +
                                              (normal_delta + math.sqrt(fiber['R']**2 - center_to_laser**2))**2)
    fiber['scattering_angle_deg']: float = 180 - phys_const.rad_to_deg(math.asin(aperture_to_laser/fiber['lens_to_point']))
    fiber['poloidal_angle_deg']: float = phys_const.rad_to_deg(math.asin(center_to_laser / fiber['R']))
    fiber['poloidal_length']: float = config['sockets'][socket_ind]['scattering_l'] * \
                                      math.cos(phys_const.deg_to_rad(fiber['poloidal_angle_deg']))
    fiber['LOS_to_center']: float = fiber['R'] * math.sin(phys_const.deg_to_rad(fiber['scattering_angle_deg']) - math.asin(center_to_laser / fiber['R']))
    fiber['LOS']: list = []
    for poly in config['poly']:
        if config['fibers'][poly['fiber']]['R'] < fiber['LOS_to_center']:
            continue
        fiber['LOS'].append({
            #'poly_ind': poly['ind'],
            'poly_serial': poly['serial'],
            'L': -math.sqrt(math.pow(config['fibers'][poly['fiber']]['R'], 2) - math.pow(fiber['LOS_to_center'], 2))
        })
        fiber['LOS'].append({
            #'poly_ind': poly['ind'],
            'poly_serial': poly['serial'],
            'L': -fiber['LOS'][-1]['L']
        })
    fiber['LOS'].sort(key=lambda entry: entry['L'])

with open('%s%s.json' % (DB_PATH, config_name), 'w') as file:
    json.dump(config, file, indent=2)

print('Geometry calculated')
