import socket
from datetime import datetime
import time
import threading
import select


class Sync:
    def __init__(self, callback):
        self.ip = "192.168.10.41"
        self.port = 8888

        self.sock = None
        self.worker = None
        self.timeout = 0.5
        self.stop = False
        self.log = []
        self.callback = callback
        self.connect()

    def connect(self):
        if self.sock:
            self.stop = True
            time.sleep(self.timeout * 2)
            self.sock.close()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((self.ip, self.port))
        self.sock.setblocking(False)

        self.worker = threading.Thread(target=self.receive)
        self.stop = False
        self.worker.start()

    def close(self):
        self.stop = True
        time.sleep(self.timeout)

    def disp(self, message):
        print('udp: ' + datetime.now().strftime("%H:%M:%S ") + message)

    def receive(self):
        while self.sock and not self.stop:
            ready_to_read, a, b = select.select(
                [self.sock],
                [],
                [],
                self.timeout)
            if len(ready_to_read):
                data = self.sock.recv(8)
                if int.from_bytes(data, 'big') == 255:
                    t = time.time()
                    self.log.append({
                        'time_f': t,
                        'time': time.localtime(t)
                    })
                    self.callback()
                    self.disp("TOKAMAK START ____________")
                else:
                    self.disp("WTF")
            else:
                continue
                self.disp("timed out")
        self.disp("udp worker exit")
