import sys
import socket
from datetime import datetime

IP = '192.168.10.44'
SOCK_TIMEOUT = 1  # timeout for network operations
TIMEOUT = 500  # watchdog timeout

BUFFER_SIZE = 16
ENCODING = 'utf-8'
PACKET_END = '\n'
SEPARATOR = ' '


class Cmd:
    local_control = '0200'
    remote_control = '0400'
    power_off = '0004'
    idle = '0012'
    desync = '100A'
    generation = '200A'
    pump_delay = '0500'
    gen_delay = '0600'
    state = '0700'
    error = '0800'


def pack(data):
    data = bytes(data + SEPARATOR, ENCODING)
    return data + bytes(crc(data) + PACKET_END, ENCODING)


def crc(packet):
    res = 0
    for byte in packet:
        res += byte
    return hex(res)[-2:].upper()


class Chatter:
    def __init__(self):
        self.connect()

    def connect(self):
        self.disp('connecting to ' + IP + ' ...')
        try:
            self.sock.connect((IP, 4001))
        except socket.timeout:
            self.disp('Connection timeout.')
            return False
        self.disp('connected')
        return True

    def disp(self, message):
        now = datetime.now()
        print(now.strftime("%H:%M:%S.%f ") + message)

    def watchdog(self):
        if self.send('J' + Cmd.state):
            self.receive()

    def send(self, packet):
        bin_packet = pack(packet)
        if self.sock.send(bin_packet) == len(bin_packet):
            return True
        self.disp('Warning! Failed to transmit packet %s as %s!' % (packet, bin_packet))
        return False

    def receive(self):
        try:
            data = self.sock.recv(BUFFER_SIZE)
        except socket.timeout:
            self.disp('Receive timeout.')
            return
        if len(data) == 0:
            self.disp('Receive failed! No response!')
        else:
            #self.disp('received: %s.' % data)
            if chr(data[-1]) != PACKET_END:
                self.disp('Wrong packet end: %s.' % data)
                return
            data = data[:-1]
            if data[-2:] != bytes(crc(data[:-2]), ENCODING):
                self.disp('Wrong CRC: %s, expected: %s.' % (data, crc(data[:-2])))
                return
            data = data[:-2]
            if chr(data[-1]) != SEPARATOR:
                self.disp('Wrong packet separator: %s.' % data)
                return
            data = data[:-1]
            cmd = chr(data[0])
            data = data[1:]
            if cmd == 'A':
                self.disp('Processing resp A: %s.' % data)
            elif cmd == 'K':
                if data[:4] == bytes(Cmd.state, ENCODING):
                    self.parse_status(int(data[4:], base=16))
                elif data[:4] == bytes(Cmd.error, ENCODING):
                    self.parse_error(int(data[4:], base=16))
                else:
                    self.disp('Unknown cmd code %s.' % data[4:])
            else:
                self.disp('Wrong cmd %s.' % cmd)

    def parse_status(self, status):
        '''
        self.disp('Status: %d' % status)
        for bit in range(16):
            self.state[bit].setChecked(1 == (status >> bit) & 1)
        if self.state[7].isChecked():
            self.state_label.setText('Аварийная остановка.')
            self.state_label.setStyleSheet("QLabel { background-color : red; color : blue; }")
        elif not self.state[0].isChecked():
            self.state_label.setText('Исходное. (контактор разомкнут)')
            self.state_label.setStyleSheet("QLabel { background-color : white; color : black; }")
            self.state_radio[0].setChecked(True)
        elif not self.state[1].isChecked():
            self.state_label.setText('Термостабилизация. (нет накачки, ЗГ отключен)')
            self.state_label.setStyleSheet("QLabel { background-color : green; color : blue; }")
            self.state_radio[1].setChecked(True)
        elif self.state[6].isChecked():
            self.state_label.setText('Холостой ход. (Накачка и ЗГ рассогласованы)')
            self.state_label.setStyleSheet("QLabel { background-color : blue; color : yellow; }")
            self.state_radio[2].setChecked(True)
        else:
            self.state_label.setText('Генерация. (Накачка и ЗГ согласованы)')
            self.state_label.setStyleSheet("QLabel { background-color : yellow; color : blue; }")
            self.state_radio[3].setChecked(True)
        '''

    def parse_error(self, error):
        '''
        self.disp('Error with code %d.' % error)
        if 1 == ((error >> 0) & 1):
            self.disp('Undocumented error. bit 0')
        if 1 == ((error >> 1) & 1):
            self.disp('Undocumented error. bit 1')
        if 1 == ((error >> 2) & 1):
            self.disp('Internal error. bit 2')
        if 1 == ((error >> 3) & 1):
            self.disp('Undocumented error. bit 3')
        if 1 == ((error >> 4) & 1):
            self.disp('Undocumented error. bit 4')
        if 1 == ((error >> 5) & 1):
            self.disp('Undocumented error. bit 5')
        if 1 == ((error >> 6) & 1):
            self.disp('Undocumented error. bit 6')
        if 1 == ((error >> 7) & 1):
            self.disp('Undocumented error. bit 7')
        if 1 == ((error >> 8) & 1):
            self.disp('Generator PSU error. bit 8')
        if 1 == ((error >> 9) & 1):
            self.disp('Generator PSU critical emergency. bit 9')
        if 1 == ((error >> 10) & 1):
            self.disp('Frequency error. bit 10')
        if 1 == ((error >> 11) & 1):
            self.disp('Connection error. bit 11')
        if 1 == ((error >> 12) & 1):
            self.disp('Cooling error. bit 12')
        if 1 == ((error >> 13) & 1):
            self.disp('Impulse counter error. bit 13')
        if 1 == ((error >> 14) & 1):
            self.disp('Undocumented error. bit 14')
        if 1 == ((error >> 15) & 1):
            self.disp('Undocumented error. bit 15')
        '''

    def parse_short_responce(self, resp):
        '''
        self.disp('Response A with code %d.' % resp)
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
        '''

    def set_state_0(self):
        self.disp('Request "Power off" state.')
        if self.send('S' + Cmd.power_off):
            self.receive()

    def set_state_1(self):
        self.disp('Request "Idle" state.')
        if self.send('S' + Cmd.idle):
            self.receive()

    def set_state_2(self):
        self.disp('Request "Desync pumping" state.')
        if self.send('S' + Cmd.desync):
            self.receive()

    def set_state_3(self):
        self.disp('Request "Generation" state.')
        if self.send('S' + Cmd.generation):
            self.receive()

    def set_remote(self):
        self.disp('Request remote control.')
        if self.send('S' + Cmd.remote_control):
            self.receive()

    def set_local(self):
        self.disp('Request local control.')
        if self.send('S' + Cmd.local_control):
            self.receive()
