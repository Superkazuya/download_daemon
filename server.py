from http import server
from socketserver import ThreadingMixIn
import threading

import cgi, cgitb
from protocol import do_request


class HTTP_server(ThreadingMixIn, server.HTTPServer):
    pass

def to_bytes(string):
    return bytes(string, "utf-8")

class HTTP_request_handler(server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path.endswith(".js"):
            with open('.'+self.path) as f:
                self.send_response(200)
                self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                self.wfile.write(to_bytes(f.read()))
                return
        elif self.path.endswith(".json"):
            if self.path == '/progress.json':
                #check ongoing tasks progresses
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(to_bytes(HTTP_request_handler.workers.get_progress()))
                return

            elif self.path == '/grunt_status.json':
                #check if there's new status, block
                #until there's status change
                wait_timeout = 40.0
                if 'ETag' in self.headers:
                    with HTTP_request_handler.workers.cv:
                        while int(HTTP_request_handler.workers.etag, 16) <= int(self.headers['ETag'], 16):
                            HTTP_request_handler.workers.cv.wait(timeout = wait_timeout)
                            self.send_response(100)
                            return

                        print("new event or onload", self.headers['ETag'])
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('ETag', HTTP_request_handler.workers.etag)
                        self.end_headers()
                        self.wfile.write(to_bytes(HTTP_request_handler.workers.get_status()))
                        return
                        
                    #timeout would return 100
            
        elif self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            ongoing = r'''
            <div class="grunt">
                <p class="progress"> Grunt {0}: </p>
                <p class="grunt_status"> > Sleeping. </p>
            </div>
                    '''
            dic = {}
            dic['ongoing'] = ''.join([ongoing.format(i) for i in range(len(HTTP_request_handler.workers))])
            dic['pending'] = ''
            dic['finished'] = ''
            with open('main.html') as f:
                self.wfile.write(to_bytes(f.read().format(**dic)))
            return

        self.send_error(404)
                    

    def do_POST(self):
        length = int(self.headers['content-length'])
        form_text = self.rfile.read(length).decode('utf-8')
        form_input = cgi.parse_qs(form_text)
        req = form_input['request']
        if not len(req) > 0:
            return
        #self.wfile.write(to_bytes(str(req)))
        req = req[0].split('\n')
        count = 0
        print(req)
        for line in req:
            #print('processing requst cmdline', line)
            ret = do_request(line, HTTP_request_handler.task_queue) 
            if(ret):
                self.wfile.write(to_bytes(ret+'\n'))
            else:
                count+=1
        if count == 1:
            self.wfile.write(to_bytes('1 request handled successfully.'))
        elif count > 1:
            self.wfile.write(to_bytes('{0} requests handled successfully. I\'m actually sooooo good.'.format(count)))
                


                    
                

            

if __name__ == '__main__':
    cgitb.enable(display = 0, logdir = '/home/superkazuya/Code/15/download_daemon/log/')
    serv = HTTP_server(("", 8080), HTTP_request_handler)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        serv.shutdown()
