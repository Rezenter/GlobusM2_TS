import socket
from datetime import datetime
import time
import threading
from pyModbusTCP.client import ModbusClient
import struct
import math

# dependencies:
#   pyModbusTCP


class Cmd:
    local_control = 'S0200'
    remote_control = 'S0400'
    power_off = 'S0004'
    idle = 'S0012'
    desync = 'S100A'
    generation = 'S200A'
    pump_delay = 'J0500'
    gen_delay = 'J0600'
    state = 'J0700'
    error = 'J0800'


def crc(packet):
    res = 0
    for byte in packet:
        res += byte
    return hex(res)[-2:].upper()


class ControlUnit:
    def __init__(self):
        self.IP = '192.168.10.44'
        self.PORT = 4001
        self.SOCK_TIMEOUT = 1  # timeout for network operations

        self.BUFFER_SIZE = 16
        self.ENCODING = 'utf-8'
        self.PACKET_END = '\n'
        self.SEPARATOR = ' '

        self.sock = None
        #self.connect()
        self.err = None
        self.state = 0
        self.lastTime = time.time()

    def connect(self):
        resp = self.status()
        if resp and resp['ok']:
            return resp
        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.SOCK_TIMEOUT)
        try:
            self.sock.connect((self.IP, self.PORT))
        except socket.timeout:
            self.set_err('Laser connection timeout.')
            return {
                'ok': False,
                'description': self.err
            }
        return self.status()

    def set_err(self, message):
        self.err = message
        self.disp(self.err)

    def disp(self, message):
        now = datetime.now()
        print('Las: ' + now.strftime("%H:%M:%S.%f ") + message)

    def pack(self, data):
        data = bytes(data + self.SEPARATOR, self.ENCODING)
        return data + bytes(crc(data) + self.PACKET_END, self.ENCODING)

    def send(self, packet):
        bin_packet = self.pack(packet)
        if not self.sock:
            self.set_err('Socket is closed.')

            print('LAS ERROR 1')

            return {
                'ok': False,
                'description': self.err
            }
        try:
            send = self.sock.send(bin_packet)
        except socket.timeout:
            self.set_err('Laser responce timeout.')

            print('LAS ERROR 2')

            return {
                'ok': False,
                'description': self.err
            }
        if send == len(bin_packet):
            recv = self.receive()
            if recv is None:
                self.set_err(self.err)

                print('LAS ERROR 3')

                return {
                    'ok': False,
                    'description': self.err
                }
            return recv

        self.set_err('Warning! Failed to transmit packet %s as %s!' % (packet, bin_packet))

        print('LAS ERROR 4')

        return {
            'ok': False,
            'description': self.err
        }

    def receive(self):
        try:
            data = self.sock.recv(self.BUFFER_SIZE)
        except socket.timeout:
            self.set_err('Receive timeout.')
            return None
        if len(data) == 0:
            self.set_err('Receive failed! No response!')
            return None
        else:
            #self.disp('received: %s.' % data)
            if chr(data[-1]) != self.PACKET_END:
                self.set_err('Wrong packet end: %s.' % data)
                return None
            data = data[:-1]
            cmd = chr(data[0])

            if cmd == 'A':
                if chr(data[-1]) != self.SEPARATOR:
                    self.set_err('Wrong packet separator: %s.' % data)
                    return None
                return {
                    'ok': True,
                    'code': int(data[1:-1])
                }
            elif cmd == 'K':
                if data[-2:] != bytes(crc(data[:-2]), self.ENCODING):
                    self.set_err('Wrong CRC: %s, expected: %s.' % (data, crc(data[:-2])))
                    return None
                data = data[1:-2]
                if chr(data[-1]) != self.SEPARATOR:
                    self.set_err('Wrong packet separator: %s.' % data)
                    return None
                data = data[:-1]

                if data[:4] == bytes(Cmd.state[1:], self.ENCODING):
                    return self.parse_status(int(data[4:], base=16))
                elif data[:4] == bytes(Cmd.error[1:], self.ENCODING):
                    return self.parse_error(int(data[4:], base=16))
                else:
                    if len(data) == 8:
                        return int(data[4:], base=16)
                    self.set_err('Unknown cmd code %s.' % data[4:])
                    return None
            else:
                self.set_err('Wrong cmd %s.' % cmd)
                return None

    def parse_status(self, status):
        self.disp('Status: %d' % status)
        state = [False for bit in range(16)]
        for bit in range(16):
            state[bit] = (1 == (status >> bit) & 1)
        timeout = -1
        if state[7]:
            self.set_err('Аварийная остановка!')
            self.state = -1
            return {
                'ok': False,
                'state': self.state,
                'timeout': timeout
            }
        elif not state[0]:
            if self.state != 0:
                self.lastTime = time.time()
            timeout = time.time() - self.lastTime
            self.state = 0
            # self.disp('Исходное. (контактор разомкнут)')
        elif not state[1]:
            if self.state != 1:
                self.lastTime = time.time()
            self.state = 1
            timeout = time.time() - self.lastTime
            # self.disp('Термостабилизация. (нет накачки, ЗГ отключен)')
        elif state[6]:
            curr_time = time.time()
            if self.state == 1:
                self.lastTime = curr_time
            self.state = 2
            timeout = 10 - curr_time + self.lastTime
            if timeout < 0:
                timeout += 60  # warm-up finished
            self.state = 2.5
            if timeout < 0:
                self.set_state_1()
            # self.disp('Холостой ход. (Накачка и ЗГ рассогласованы)')
        else:
            timeout = 10 + 60 - time.time() + self.lastTime
            self.state = 3
            if timeout < 0:
                self.set_state_1()
            # self.disp('Генерация. (Накачка и ЗГ согласованы)')

        return {
            'ok': True,
            'state': self.state,
            'timeout': timeout,
            'flags': state
        }

    def parse_error(self, error):
        flag = False
        self.disp('Laser-side error with code %d.' % error)
        if 1 == ((error >> 0) & 1):
            self.set_err('Undocumented error. bit 0')
        if 1 == ((error >> 1) & 1):
            self.set_err('Undocumented error. bit 1')
        if 1 == ((error >> 2) & 1):
            self.set_err('Internal error. bit 2')
        if 1 == ((error >> 3) & 1):
            self.set_err('Undocumented error. bit 3')
        if 1 == ((error >> 4) & 1):
            self.set_err('Undocumented error. bit 4')
        if 1 == ((error >> 5) & 1):
            self.set_err('Undocumented error. bit 5')
        if 1 == ((error >> 6) & 1):
            self.set_err('Undocumented error. bit 6')
        if 1 == ((error >> 7) & 1):
            self.set_err('Undocumented error. bit 7')
        if 1 == ((error >> 8) & 1):
            self.set_err('Generator PSU error. bit 8')
        if 1 == ((error >> 9) & 1):
            self.set_err('Generator PSU critical emergency. bit 9')
        if 1 == ((error >> 10) & 1):
            self.set_err('Frequency error. bit 10')
        if 1 == ((error >> 11) & 1):
            self.set_err('Connection error. bit 11')
        if 1 == ((error >> 12) & 1):
            self.set_err('Cooling error. bit 12')
        if 1 == ((error >> 13) & 1):
            self.set_err('Impulse counter error. bit 13')
        if 1 == ((error >> 14) & 1):
            self.set_err('Undocumented error. bit 14')
        if 1 == ((error >> 15) & 1):
            self.set_err('Undocumented error. bit 15')
        return {
            'ok': flag,
            'description': self.err
        }

    def parse_short_responce(self, resp):
        self.disp('Short response: %d' % resp)
        if resp == 0:
            self.disp('CMD ok.')
        elif resp == 1:
            self.disp('CMD ok, put in queue.')
        elif resp == 2:
            self.disp('CMD correct, but dismissed.')
        elif resp == 3:
            self.disp('CMD parameters are incorrect.')
        elif resp == 4:
            self.disp('CMD execution is prohibited.')
        elif resp == 5:
            self.disp('CMD wrong, unknown reason.')
        elif resp == 6:
            self.disp('CMD wrong, format.')
        elif resp == 7:
            self.disp('CRC error.')
        elif resp < 16:
            self.disp('Undocumented error.')
        else:
            self.disp('Error in this code.')

    def set_state_0(self):
        self.disp('Request "Power off" state.')
        return self.send(Cmd.power_off)

    def set_state_1(self):
        self.disp('Request "Idle" state.')
        return self.send(Cmd.idle)

    def set_state_2(self):
        self.disp('Request "Desync pumping" state.')
        return self.send(Cmd.desync)

    def set_state_3(self):
        self.disp('Request "Generation" state.')
        return self.send(Cmd.generation)

    def set_remote(self):
        self.disp('Request remote control.')
        return self.send(Cmd.remote_control)

    def set_local(self):
        self.disp('Request local control.')
        return self.send(Cmd.local_control)

    def status(self):
        return self.send(Cmd.state)

    def get_energy(self):
        res = {
            'pump': self.send(Cmd.pump_delay),
            'gen': self.send(Cmd.gen_delay)
        }
        return res


class Coolant:
    def __init__(self):
        self.dt = 1

        self.ip = "192.168.10.47"
        self.port = 502
        self.unit_id = 2

        self.client = None
        self.worker = None
        self.log = []
        self.log_size = math.ceil(60 * 15 / self.dt)
        self.connect()

    def __connect(self):
        if self.client and self.client.is_open():
            self.close()
        self.client = ModbusClient(host=self.ip, port=self.port, unit_id=self.unit_id, auto_open=True)
        self.client.read_input_registers(30, 2)  # needed for is_open function
        if not self.client.is_open():
            return

        self.worker = threading.Thread(target=self.receive)
        self.disp('coolant connected')
        self.worker.start()

    def connect(self):
        task = threading.Thread(target=self.__connect)
        task.start()

    def close(self):
        self.client.close()
        time.sleep(self.dt)

    def disp(self, message):
        print('coolant: ' + datetime.now().strftime("%H:%M:%S ") + message)

    def receive(self):
        while self.client.is_open():
            resp = self.client.read_input_registers(30, 2)
            if resp:
                f = resp[0].to_bytes(2, 'big')
                s = resp[1].to_bytes(2, 'big')

                t = time.time()
                self.log.append({
                    'temperature': struct.unpack('>f', s + f)[0],
                    'time_f': t,
                    'time': time.localtime(t)
                })
                if len(self.log) > self.log_size:
                    self.log.pop(0)

            time.sleep(self.dt)
        self.disp("coolant worker exit")
