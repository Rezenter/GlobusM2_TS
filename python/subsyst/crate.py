import socket
from datetime import datetime
import time
import threading
import select


class Crate:
    "$CMD:SET,CH:8,PAR:ON"  # control power
    '$CMD:SET,CH:8,PAR:OFF'

    def __init__(self):
        self.dt = 60
        self.timeout = 0.5

        self.ip = '192.168.10.43'
        self.port = 8100

        self.sock = None
        self.worker = None
        self.log = []
        self.stop = False
        self.connect()

    def close(self):
        self.stop = True
        time.sleep(self.dt)

    def connect(self):
        if self.sock:
            self.stop = True
            time.sleep(self.timeout * 2)
            self.sock.close()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        self.sock.setblocking(False)

        self.worker = threading.Thread(target=self.request)
        self.stop = False
        self.worker.start()

    def disp(self, message):
        print('crate: ' + datetime.now().strftime("%H:%M:%S ") + message)

    def request(self):
        while self.sock and not self.stop:
            self.sock.sendall(b'$CMD:MON,CH:8,PAR:PSTEMP\r\n')
            ready_to_read, ready_to_write, in_error = select.select(
                [self.sock],
                [],
                [],
                self.timeout)
            if len(ready_to_read):
                resp = self.sock.recv(64).decode()
                temp = int(resp.split(':')[-1])

                '''
File "D:\code\TomsonViewer\python\subsyst\crate.py", line 56, in request
temp = int(resp.split(':')[-1])
ValueError: invalid literal for int() with base 10: ''
                '''
            else:
                continue

            self.sock.sendall(b'$CMD:MON,CH:8,PAR:FUTEMP\r\n')
            ready_to_read, ready_to_write, in_error = select.select(
                [self.sock],
                [],
                [],
                self.timeout)
            if len(ready_to_read):
                resp = self.sock.recv(64).decode()
                fan_temp = int(resp.split(':')[-1])
            else:
                continue

            self.sock.sendall(b'$CMD:MON,CH:8,PAR:CRST\r\n')
            ready_to_read, ready_to_write, in_error = select.select(
                [self.sock],
                [],
                [],
                self.timeout)
            if len(ready_to_read):
                resp = self.sock.recv(64).decode()
                error = (int(resp.split(':')[-1])).to_bytes(2, 'big')
                online = bool(error[1] & 0x01)
                is_error = bool(error[0] & 0b11111101) or bool(error[1] & 0b11111110)
            else:
                continue

            t = time.time()
            self.log.append({
                'temperature_ps': temp,
                'temperature_fan': fan_temp,
                'online': online,
                'error': is_error,
                'time': t,
                'time_f': time.localtime(t)
            })
            #print(self.log[-1])
            time.sleep(self.dt)
        self.disp("crate worker exit")
