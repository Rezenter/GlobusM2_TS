import socket
from time import sleep


class Ophir:
    HOST = '192.168.10.55'
    PORT = 8888
    SOCK_TIMEOUT = 1  # timeout for network operations
    BUFFER_SIZE = 64
    ENCODING = 'utf-8'

    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print('Connecting ophir...')
            s.settimeout(0.1)
            s.connect((self.HOST, self.PORT))
            try:
                s.sendall(b'connect')
                sleep(1)
            except socket.timeout:
                print('socket timeout')

    def status(self) -> dict:
        res = {
            'ok': False,
            'connected': False,
            'ready': False,
            'armed': False
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            s.settimeout(0.1)
            try:
                s.sendall(b'status')
                data = s.recv(64)
                if len(data) > 0:
                    status = int.from_bytes(bytes=data, byteorder='big', signed=True)
                    if status == 0:
                        res['connected'] = True
                        res['ready'] = True
                        res['armed'] = False
                    elif status == 1:
                        res['connected'] = True
                        res['ready'] = False
                        res['armed'] = True
                    elif status == 2:
                        res['connected'] = True
                        res['ready'] = False
                        res['armed'] = False
                    else:
                        res['connected'] = False
                        res['ready'] = False
                        res['armed'] = False
            except socket.timeout:
                print('socket timeout')
        return res

    def arm(self, is_plasma: bool, shotn: int):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            s.settimeout(0.1)
            print('Connecting ophir...')
            try:
                s.sendall(('arm %d %d' % (is_plasma, shotn)).encode('utf-8'))
                sleep(1)
            except socket.timeout:
                print('socket timeout')

    def disarm(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            s.settimeout(0.1)
            print('Connecting ophir...')
            try:
                s.sendall(b'disarm')
                sleep(1)
            except socket.timeout:
                print('socket timeout')
