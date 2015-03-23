from http import server
from socketserver import ThreadingMixIn
import cgi, cgitb
from protocol import do_request
import json

from events import event_list
from snapshot import summary


class HTTP_server(ThreadingMixIn, server.HTTPServer):
    pass

def to_bytes(string):
    return bytes(string, "utf-8")

class HTTP_request_handler(server.BaseHTTPRequestHandler):
    def handle(self):
        try:
            return server.BaseHTTPRequestHandler.handle(self)
        except BrokenPipeError:
            print(">>>>> BrokenPipe?", BrokenPipeError.args)
        except (server.socket.error, server.socket.timeout) as e:
            print("connection dropped", e.args)

    def do_GET(self):
        if self.path.endswith(".js"):
            with open('.'+self.path) as f:
                self.send_response(200)
                self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                self.wfile.write(to_bytes(f.read()))
                return
        elif self.path == '/progress':
            #check ongoing tasks progresses
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(to_bytes(HTTP_request_handler.workers.get_progress()))
            return

        elif self.path == '/events':
            #moreee consumers
            self.protocol_version = 'HTTP/1.1'
            self.new_connection = True
            self.send_response(200)
            self.send_header('content-type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()

            
            if 'Last-Event-ID' in self.headers:
                #it's a reconnect
                #strangely, it's up to the server to decide if all task status should be sent
                last_event_id = self.headers['Last-Event-ID']
                print("last_event_id in headers", last_event_id)
                try:
                    event = event_list[last_event_id]
                    print(event)
                    self.new_connection = False
                except KeyError:
                    self.new_connection = True
            
            if self.new_connection:
                self.wfile.write(to_bytes('event: summary'))
                with summary.mutexlock:
                    #will only block when it's a new connection. But still it's blocking
                    eid = summary.newest_ev_node.event_id
                    data = json.dumps(summary)
                    event = summary.newest_ev_node
                self.wfile.write(to_bytes('\nid: {0} \ndata: {1}'.format(eid, data)))
                self.wfile.write(to_bytes('\n\n'))
                print("new summary data", data)

            print("is it a new connection?", self.new_connection)

            while True:
                while not (event._next is event_list.sentinel):
                    next_event = event._next
                    self.wfile.write(to_bytes('event: update'))
                    #event_string += event.task.identifier
                    self.wfile.write(to_bytes('\nid: '))
                    self.wfile.write(to_bytes(next_event.event_id))
                    self.wfile.write(to_bytes('\ndata: '))
                    json_data = json.dumps(next_event.to_dict())
                    self.wfile.write(to_bytes(json_data))
                    self.wfile.write(to_bytes('\n\n'))
                    print(json_data)
                    #print('event_string',event_string)
                    #print('event_list count', event_list.count)
                    event = next_event
                        
           
        elif self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            dic = {}
            dic['active'] = ''
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
