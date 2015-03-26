from http import server
from socketserver import ThreadingMixIn
import cgi
from protocol import do_request
import json
import threading

from events import event_list, summary
from task_collection import existing_task_dict

class HTTP_server(ThreadingMixIn, server.HTTPServer):
    pass

def to_bytes(string):
    return bytes(string, "utf-8")

class HTTP_request_handler(server.BaseHTTPRequestHandler):
    def handle(self):
        try:
            return server.BaseHTTPRequestHandler.handle(self)
        except BrokenPipeError:
            #some client disconnected during the HTTP stream
            print('active threads num', threading.active_count())
        except (server.socket.error, server.socket.timeout) as e:
            print('-'*40)
            print("connection dropped", e.args)

    def do_GET(self):
        print('active threads num', threading.active_count())
        if self.path.endswith(".js"):
            with open('.'+self.path) as f:
                self.send_response(200)
                self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                self.wfile.write(to_bytes(f.read()))

        elif self.path == '/events':
            #moreee consumers
            #self.protocol_version = 'HTTP/1.1'
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
                    self.newest_ev_node = event_list[last_event_id]
                    print(self.newest_ev_node)
                    self.new_connection = False
                except KeyError:
                    self.new_connection = True

            
            if self.new_connection:
                self.wfile.write(to_bytes('event: summary'))
                with summary.mutexlock:
                    #will only block when it's a new connection. But still it's blocking
                    event_list.users[id(self)] = self
                    self.newest_ev_node = summary.newest_ev_node
                    data = json.dumps(summary)
                    #it's a garbage collection thing
                self.wfile.write(to_bytes('\nid: {0} \ndata: {1}'.format(self.newest_ev_node.event_id, data)))
                self.wfile.write(to_bytes('\n\n'))
                print("provide the new connection with summary data", data)

            while True:
                if not self.newest_ev_node._next is event_list.sentinel:
                    next_event = self.newest_ev_node._next
                    self.wfile.write(to_bytes('event: update'))
                    self.wfile.write(to_bytes('\nid: '))
                    self.wfile.write(to_bytes(next_event.event_id))
                    self.wfile.write(to_bytes('\ndata: '))
                    json_data = json.dumps(next_event.to_dict())
                    self.wfile.write(to_bytes(json_data))
                    self.wfile.write(to_bytes('\n\n'))
                    self.newest_ev_node = next_event
                else:
                    event_list.new_event.wait(2)
                    self.wfile.write(to_bytes('event: test'))
                    self.wfile.write(to_bytes('\ndata: '))
                    self.wfile.write(to_bytes('are you alive?'))
                    self.wfile.write(to_bytes('\n\n'))
           
        elif self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            dic = {}
            dic['active'] = ''
            dic['pending'] = ''
            dic['finished'] = ''
            with open('main.html', 'r') as f:
                self.wfile.write(to_bytes(f.read().format(**dic)))
        else:
            self.send_error(404)
                    

    def do_POST(self):
        length = int(self.headers['content-length'])
        form_text = self.rfile.read(length).decode('utf-8')
        form_input = cgi.parse_qs(form_text)
        #print(form_input)
        if 'request' in form_input:
            req = form_input['request']
            if not len(req) > 0:
                return
            #self.wfile.write(to_bytes(str(req)))
            req = req[0].split('\n')
            count = 0
            for line in req:
                if not line:
                    continue
                #print('processing requst cmdline', line)
                ret = do_request(line) 
                if(ret):
                    self.wfile.write(to_bytes(ret+'\n'))
                else:
                    count+=1
            if count == 1:
                self.wfile.write(to_bytes('1 request handled successfully.'))
            elif count > 1:
                self.wfile.write(to_bytes('{0} requests handled successfully.'.format(count)))
        elif 'pause' in form_input:
            try:
                existing_task_dict[form_input['pause'][0]].pause()
            except KeyError:
                print('jabroni outfit')

        elif 'resume' in form_input:
            try:
                existing_task_dict[form_input['resume'][0]].resume()
            except KeyError:
                print('jabroni outfit')
        elif 'cancel' in form_input:
            try:
                existing_task_dict[form_input['cancel'][0]].cancel()
            except KeyError:
                print('jabroni outfit')
        else:
            self.wfile.write(to_bytes('fuck you leather man.'))
            
                 
if __name__ == '__main__':
    serv = HTTP_server(("", 8080), HTTP_request_handler)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        serv.shutdown()

