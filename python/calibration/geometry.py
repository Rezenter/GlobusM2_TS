import json
import math
import phys_const

DB_PATH: str = 'd:/data/db/'
SOCKET_FOLDER: str = 'sockets/'
FIBER_FOLDER: str = 'fibers/'
PROCESSED_FOLDER: str = 'calculated/'
JSON: str = '.json'

aperture_to_laser: float = 681.3  # mm. normal length from lens to the probing chord
center_to_laser: float = 169.6  # normal length from the tokamak center to the probing chord
normal_delta: float = 184.3  # distance between the normals

# change only these two lines!
sockets_name: str = '2022.06.07'
fibers_name: str = '2022.06.03'
# change only these two lines!


result: dict = {
    'type': 'Calculated fiber geometry',
    'type version': 1,
    'sockets': {
        'file': sockets_name,
        'data': []
    },
    'fibers': {
        'file': fibers_name,
        'data': []
    }
}

with open('%s%s%s%s' % (DB_PATH, SOCKET_FOLDER, sockets_name, JSON), 'r') as file:
    result['sockets'] = json.load(file)

with open('%s%s%s%s' % (DB_PATH, FIBER_FOLDER, fibers_name, JSON), 'r') as file:
    result['fibers'] = json.load(file)

for fiber in result['fibers']:
    socket_ind: int = 0
    for socket_ind in range(len(result['sockets'])):
        if result['sockets'][socket_ind]['lens_socket'] == fiber['lens_socket']:
            break
    else:
        print('Socket "%s" not found.' % fiber['lens_socket'])
        fuck
    fiber['lens_socket_ind']: int = socket_ind
    fiber['lens_to_point']: float = math.sqrt(aperture_to_laser**2 +
                                              (normal_delta + math.sqrt(fiber['R']**2 - center_to_laser**2))**2)
    fiber['scattering_angle_deg']: float = 180 - phys_const.rad_to_deg(math.asin(aperture_to_laser/fiber['lens_to_point']))
    fiber['poloidal_angle_deg']: float = phys_const.rad_to_deg(math.asin(center_to_laser / fiber['R']))
    fiber['poloidal_length']: float = result['sockets'][socket_ind]['scattering_l'] * \
                                      math.cos(phys_const.deg_to_rad(fiber['poloidal_angle_deg']))

with open('%s%s%s%s%s' % (DB_PATH, FIBER_FOLDER, PROCESSED_FOLDER, fibers_name, JSON), 'w') as file:
    json.dump(result, file, indent=4)

print('Geometry calculated')
