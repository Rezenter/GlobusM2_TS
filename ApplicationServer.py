import http.server
import json
from python.RequestHandler import Handler
import mimetypes
import ssl
from pathlib import Path

handler = Handler()

mimetypes.init()
mimetypes.add_type('text/javascript', '.js', strict=True)


def __init__():
    return


class ApplicationServer (http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        uri = self.requestline.split(' ')[1]
        if uri != '/api':
            print('Wrong API uri: {0}'.format(uri))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps({
                'ok': False,
                'description': 'Wrong API uri'
            }), 'utf-8'))
            return

        bodyLength = int(self.headers.get('content-length', 0))
        body = self.rfile.read(bodyLength).decode('utf-8')
        parsedBody = {}
        try:
            parsedBody = json.loads(body)
        except:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Error 400: Not a JSON request')
            return

        if 'req' in parsedBody and parsedBody['req'] == 'sht':
            if 'shotn' not in parsedBody:
                self.send_error(404, 'Shotn was not specified!')
                return
            shotn = parsedBody['shotn']
            path = Path('D:/data/db/plasma/result/%s/TS_%s.sht' % (shotn, shotn))
            if not path.is_file():
                self.send_error(404, 'File Not Found: %s ' % path)
                return
            with open(path, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                for s in file:
                    self.wfile.write(s)
            return

        resp = handler.handle_request(parsedBody)

        #print('Sending response: ')
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(resp), 'utf-8'))

    def do_GET(self):
        filepath = ''
        try:
            if self.path in ("", "/"):
                filepath = "index.html"
            else:
                filepath = self.path.lstrip("/")
            f = open('html/%s' % filepath, "rb")
        except IOError:
            self.send_error(404, 'File Not Found: %s ' % filepath)

        else:
            self.send_response(200)
            #this part handles the mimetypes for you.
            mimetype, _ = mimetypes.guess_type(filepath)
            #print(mimetype)
            self.send_header('Content-type', mimetype)
            self.end_headers()
            for s in f:
                self.wfile.write(s)
            f.close()

if __name__ == '__main__':
    server = http.server.HTTPServer

    httpd = server(('', 443), ApplicationServer)
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile='privatekey.key', certfile='certificate.pem', server_side=True)
    try:
        print('Serving from now.')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
