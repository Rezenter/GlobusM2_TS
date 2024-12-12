from datetime import datetime
import time
import requests
import json


class ControlUnit:
    def __init__(self):
        self.cpp_url = "http://192.168.10.60:80/api"

        self.state = 0
        self.lastTime = time.time()

    def connect(self):
        return self.status()


    def disp(self, message):
        now = datetime.now()
        print('Las: ' + now.strftime("%H:%M:%S.%f ") + message)

    def set_state_0(self):
        self.disp('Request "Power off" state.')
        return requests.post(self.cpp_url, data=json.dumps({
            "subsystem": 'laser330',
            'reqtype': 'setState',
            'target': 0
        })).json()

    def set_state_1(self):
        self.disp('Request "Idle" state.')
        return requests.post(self.cpp_url, data=json.dumps({
            "subsystem": 'laser330',
            'reqtype': 'setState',
            'target': 1
        })).json()

    def set_state_2(self):
        self.disp('Request "Desync pumping" state.')
        return requests.post(self.cpp_url, data=json.dumps({
            "subsystem": 'laser330',
            'reqtype': 'setState',
            'target': 2
        })).json()

    def set_state_3(self):
        self.disp('Request "Generation" state.')
        return requests.post(self.cpp_url, data=json.dumps({
            "subsystem": 'laser330',
            'reqtype': 'setState',
            'target': 3
        })).json()

    def status(self):
        #print('requested status')
        #tmp =
        #print(tmp)

        resp = requests.post(self.cpp_url, data=json.dumps({
            "subsystem": 'laser330',
            'reqtype': 'status'
        })).json()
        resp['coolant'] = requests.post(self.cpp_url, data=json.dumps({
            "subsystem": 'coolant',
            'reqtype': 'status'
        })).json()
        return resp

    def get_energy(self):
        return requests.post(self.cpp_url, data=json.dumps({
            "subsystem": 'laser330',
            'reqtype': 'delays'
        })).json()
        '''
        res = {
            'pump': self.send(Cmd.pump_delay),
            'gen': self.send(Cmd.gen_delay)
        }
        return res'''