import socket
import subprocess
from pathlib import Path


class SlowADC:
    PORT = 3425
    user = 'root'
    secret = 'terasic'

    ADC_IP = [
        '192.168.10.50',
        '192.168.10.51',
        '192.168.10.52',
        '192.168.10.53',
    ]

    COMMANDS = {
        'status': b'\x0c',
        'trigger_start_10v': b'\x02\x05\x00\x2c\x02',
        'soft_start_10v': b'\x02\x04\x00\x2c\x02',
        'trigger_start_5v': b'\x02\x05\x01\x2c\x02',
        'soft_start_5v': b'\x02\x04\x01\x2c\x02',
        'soft_trigger': b'\x04',
    }

    def __init__(self, path: str):
        self.DB = Path(path)
        self.ready = False
        self.current_path = self.DB

        if not self.current_path.is_dir():
            print(f'DB path "{self.current_path}" is invalid.')
            return

        print('Connecting to slow ADCs...')
        for ip in self.ADC_IP:
            if self.__status(ip) != b'\x00':
                print(f'{ip} not initialised!')
                break
        else:
            print('Connected.')
            self.ready = True

    def arm(self, shotn: int):
        """
        Arm all ADCs for trigger-based acquisition, 10V range.
        """
        self.current_path = Path('%s/sht%05d' % (self.DB, shotn))
        self.current_path.mkdir(exist_ok=True)
        for ip in self.ADC_IP:
            self._send_command(ip, self.COMMANDS['trigger_start_10v'])  # trigger start, 10V
            print(f'{ip} ARMED')

    def disarm(self):
        """
        Disarm ADCs and retrieve data if ready.
        """
        success: int = 0
        for ip in self.ADC_IP:
            if self.__status(ip) != b'\x4b':
                print(ip, 'not ready!')
            success += 1
            self.get_data(ip)

        if success == len(self.ADC_IP):
            print('Slow ADC disarmed OK')
        else:
            print(f'Only {success} of {len(self.ADC_IP)} slow ADCs ready')

    def status(self):
        """
        Check if all ADCs are in initial state.
        """
        if not self.ready:
            return False

        return all(self.__status(ip) == b'\x00' for ip in self.ADC_IP)

    def __status(self, ip: str):
        """
        Request status from ADC board.
        """
        with socket.socket() as sock:
            sock.connect((ip, self.PORT))
            sock.send(self.COMMANDS['status'])
            data = sock.recv(2048)
            print(f'Slow ADC {ip} status', data[1:])
        return data[1:]

    def get_data(self, board: int):
        print(f'{self.current_path}/{board}.slow')
        subprocess.run(
            ["pscp", "-pw", self.secret, "-batch", '-C', '%s@%s:adc_data.slow' % (self.user, self.ADC_IP[board]),
             '%s/%s.slow' % (self.current_path, self.ADC_IP[board])])

    def soft_arm(self, shotn: int):
        """
        Arm all ADCs for software-based acquisition, 5V range.
        """
        self.current_path = Path(f'%s/sht%05d' % (self.DB, shotn))
        self.current_path.mkdir(exist_ok=True)

        for ip in self.ADC_IP:
            self._send_command(ip, self.COMMANDS['soft_start_5v'])

    def soft_trig(self):
        """
        Trigger all ADCs via software.
        """
        for ip in self.ADC_IP:
            self._send_command(ip, self.COMMANDS['soft_trigger'])

    def _send_command(self, ip: str, command: bytes):
        """
        Open socket and send a raw command to ADC.
        """
        with socket.socket() as sock:
            sock.connect((ip, self.PORT))
            sock.send(command)
