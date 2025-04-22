import socket
import json
import time

class MySocket:

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def mysend(self, msg):
        totalsent = 0
        b_mes = str.encode(msg)
        while totalsent < len(msg):
            sent = self.sock.send(b_mes[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def myreceive(self):
        chunks = []
        bytes_recd = 0

        chunk = self.sock.recv(40000)
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)


print('start')

sock = MySocket()
sock.connect(host='192.168.10.64', port=4080)

start = -9

while 1:
    sock.mysend(json.dumps({"ok": 1}))
    time.sleep(1)
    str_rec = sock.myreceive()
    #print(str)
    data = json.loads(str_rec)
    if start == -9:
        start = data[0]['timestamp']
    print(data[0]['timestamp'] - start, data[0]['PSU']['V'])

print('OK')
