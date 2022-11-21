import sys
import datetime
import socket
from bitstring import BitArray
import subprocess
import time
import os

ADC_IP = ['192.168.10.50',
          '192.168.10.51',
          '192.168.10.52',
          '192.168.10.53']

PORT = 3425
user = 'root'
secret = 'terasic'


def connection(board: int):
    sock = socket.socket()
    sock.connect((ADC_IP[board], PORT))
    print('Slow ADC = %d connected' % board)
    #sock.send(b'\x02\x04\x00\x2c\x02') #запуск от soft, 10В диап
    sock.send(b'\x02\x05\x00\x2c\x02') #настройки, запуск от триггера, 10В диап
    #sock.send(b'\x02\x05\x01\x2c\x03') #настройки, запуск от триггера, 5В диап
    #print('ADC_ip = %s configured' % ip)
    sock.close()


def check_status(board: int):
    sock = socket.socket()
    sock.connect((ADC_IP[board], PORT))
    sock.send(b'\x0c')
    data = sock.recv(2048)
    #data = BitArray(data[1:])
    print('Slow ADC %d status ' % board, BitArray(data[1:]))
    sock.close()
    return BitArray(data[1:])


def get_data(board: int, path: str):
    subprocess.run(["pscp", "-pw", secret, '%s@%s:adc_data.slow' % (user, ADC_IP[board]), '%s/%s.slow' % (path, ADC_IP[board])])

