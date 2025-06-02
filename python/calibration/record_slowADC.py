import socket
import subprocess
from pathlib import Path
import time
import os

fiber = '3_fixed'
repeat = 20

class SlowADC:
    PORT = 3425
    user = 'root'
    secret = 'terasic'

    ADC_IP = ['192.168.10.50',
              '192.168.10.51',
              '192.168.10.52',
              '192.168.10.53']

    fingerprint = 'ecdsa-sha2-nistp256 256 SHA256:dwbpGGyAksQiqqLe0QwW4CTuT9HRlZgkm2NCKdWKwYA'


    def __init__(self, path: str):
        self.DB = path
        self.ready = False
        self.current_path = Path('%s/' % self.DB)
        if not self.current_path.is_dir():
            print('DB path "%s" is invalid.' % self.current_path)
            return
        print('Connecting to slow ADCs...')
        for ip_ind in range(len(self.ADC_IP)):
            if self.__status(ip_ind) != b'\x00':
                print(self.ADC_IP[ip_ind], 'not initialised!')
                break
        else:
            print('Connected.')
            self.ready = True

    def arm(self, shotn: int):
        self.current_path = Path('%s/sht%05d' % (self.DB, shotn))
        self.current_path.mkdir(exist_ok=True)
        for ip in self.ADC_IP:
            sock = socket.socket()
            sock.connect((ip, self.PORT))
            #sock.send(b'\x02\x04\x00\x2c\x02') #запуск от soft, 10В диап
            sock.send(b'\x02\x05\x00\x2c\x02') #настройки, запуск от триггера, 10В диап
           #sock.send(b'\x02\x05\x01\x2c\x02') #настройки, запуск от триггера, 5В диап
            #print('ADC_ip = %s configured' % ip)
            sock.close()
            print(ip, ' ARMED')

    def disarm(self):
        success: int = 0
        for ip_ind in range(len(self.ADC_IP)):
            if self.__status(ip_ind) != b'\x4b':
                print(self.ADC_IP[ip_ind], 'not ready!')
                #continue
            success += 1
            self.get_data(ip_ind)
        if success == len(self.ADC_IP):

            print('slow ADC disarmed OK')
        else:
            print('Only %d of %d slow ADCs ready' % (success, len(self.ADC_IP)))

    def satus(self):
        if not self.ready:
            return False
        for ip_ind in range(len(self.ADC_IP)):
            if self.__status(ip_ind) != b'\x00':
                return False
        return True

    def __status(self, board: int):
        sock = socket.socket()
        sock.connect((self.ADC_IP[board], self.PORT))
        sock.send(b'\x0c')
        data = sock.recv(2048)
        print('Slow ADC %d status ' % board, data[1:])
        sock.close()
        return data[1:]

    def get_data(self, board: int):
        print('%s/%s.slow' % (self.current_path, self.ADC_IP[board]))
        subprocess.run(["pscp", "-pw", self.secret, "-hostkey", self.fingerprint, "-batch", '-C', '%s@%s:adc_data.slow' % (self.user, self.ADC_IP[board]), '%s/%s.slow' % (self.current_path, self.ADC_IP[board])])
        # to sht

    def soft_arm(self, shotn: int):
        self.current_path = Path('%s/sht%05d' % (self.DB, shotn))
        self.current_path.mkdir(exist_ok=True)
        for ip in self.ADC_IP:
            sock = socket.socket()
            sock.connect((ip, self.PORT))
            #sock.send(b'\x02\x04\x00\x2c\x02') #запуск от soft, 10В диап
            sock.send(b'\x02\x04\x01\x2c\x02') #запуск от soft, 5В диап
            sock.close()

    def soft_trig(self):
        for ip in self.ADC_IP:
            sock = socket.socket()
            sock.connect((ip, self.PORT))
            sock.send(b'\x04') #запуск от soft
            sock.close()


os.mkdir('slow\\%s' % fiber)
adc = SlowADC('slow\\%s' % fiber)
time.sleep(2)

for shotn in range(repeat):
    adc.soft_arm(shotn=shotn)
    time.sleep(2)
    adc.soft_trig()
    time.sleep(2)
    adc.disarm()

print('final')
