from http import server
from socketserver import ThreadingMixIn
from urllib import parse
from protocol import form
import json
import threading
import logging

from events import event_list, summary
#from task_collection import existing_task_dict

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
            logging.info('active threads num %d', threading.active_count())
        except (server.socket.error, server.socket.timeout) as e:
            logging.exception("connection dropped %s", e.args)

    def do_GET(self):
        logging.info('active threads num %d', threading.active_count())
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
                logging.info("last_event_id in headers: %s", last_event_id)
                try:
                    self.newest_ev_node = event_list[last_event_id]
                    logging.info('Find matching ev node: %s', self.newest_ev_node)
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
                logging.info("provide the new connection with summary data %s", str(data))

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
        form_input = parse.parse_qs(form_text)
        ret = form.process(form_input)
        try:
            self.wfile.write(to_bytes(ret))
        except TypeError:
            pass
            
                 
if __name__ == '__main__':
    serv = HTTP_server(("", 8080), HTTP_request_handler)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        serv.shutdown()

