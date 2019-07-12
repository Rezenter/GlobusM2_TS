import http.server
import json
from RequestHandler import Handler

handler = Handler()

def __init__():
    return

class ApplicationServer (http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        uri = self.requestline.split(' ')[1]
        if uri != '/api':
            print ('Wrong API uri: {0}'.format(uri))

        print ('Handling POST request: ')
        bodyLength = int(self.headers.get('content-length', 0))
        body = self.rfile.read(bodyLength).decode('utf-8')
        parsedBody = []
        try:
            parsedBody = json.loads(body)
        except:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Error 400: Not a JSON request')

        resp = handler.HandleRequest(parsedBody)

        print ('Sending response: ')
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(resp), 'utf-8'))


if __name__ == '__main__':
    server = http.server.HTTPServer
    httpd = server(('', 8081), ApplicationServer)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()