from multiprocessing.pool import ThreadPool
from threading import Thread, Timer
from server import HTTP_request_handler, HTTP_server
import cgitb
from queue import Queue
from protocol import do_request
from events import event_list, summary

task_queue = Queue()

#dirty?
# synchronization in long-polling
thread_num = 5

HOST, PORT = 'localhost', 8080

class grunt:
    def __init__(self):
        #print('work work')
        #check if there's a status change
        self.task = None
        #atomic?
        while True:
            self.task = task_queue.get()
            self.task.start()
            self.task = None
            task_queue.task_done()


def apply_async_callback(arg):
    pass
    #print(arg.url)

def apply_async_error_callback(arg):
    #print("error", arg)
    pass
    
if __name__ == '__main__':
    thread_pool = ThreadPool(thread_num)
    for i in range(thread_num):
        thread_pool.apply_async(grunt, callback=apply_async_callback, error_callback=apply_async_error_callback)

    summary_generating_thread = Thread(target = summary.update_all)
    summary_generating_thread.start()
    event_list.garbage_collection()
    

    HTTP_request_handler.task_queue = task_queue
    serv = HTTP_server(("", 8080), HTTP_request_handler)
    #generate ETag when init
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        pass

    finally:
            serv.shutdown()
            summary_generating_thread.join()
            thread_pool.close()
            thread_pool.join()
        

