from multiprocessing.pool import ThreadPool
from server import HTTP_request_handler, HTTP_server
from threading import Condition
import cgitb
from queue import Queue
from protocol import do_request
import json
import datetime

task_queue = Queue()

class task_list(list):
    def get_progress(self):
        progress = []
        for worker in self:
            if worker.task:
                progress.append(worker.task.get_progress())
            else:
                progress.append([])

        return json.dumps(progress)

    def get_status(self):
        status = [[], []]
        for worker in self:
            if worker.task:
                status[0].append(worker.task.get_status())
            else:
               status[0].append([])
        if not task_queue.empty():
            for i in task_queue.queue:
                status[1].append(i.get_status())
            #dangerous?
        return json.dumps(status)

    def generate_etag(self):
        t = datetime.datetime.now()
        t = t - datetime.datetime(2015, 3, 14)
        t /= datetime.timedelta(microseconds=1)
        return hex(int(t))[2:]


    def get_status_on_change(self):
        #this function will be called when there's a status change
        with self.cv:
            self.etag = self.generate_etag()
            #etag for the change
            self.get_status()
            self.cv.notify_all()


worker_list = task_list()
worker_list.cv = Condition()
#dirty?
# synchronization in long-polling
thread_num = 5

HOST, PORT = 'localhost', 8080

class grunt:
    def __init__(self):
        #print('work work')
        #check if there's a status change
        worker_list.append(self)
        self.task = None
        #atomic?
        while True:
            self.task = task_queue.get()
            worker_list.get_status_on_change()
            self.task.start()
            self.task = None
            worker_list.get_status_on_change()
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

    cgitb.enable(display = 0, logdir = '/home/superkazuya/Code/15/download_daemon/')

    HTTP_request_handler.workers = worker_list
    HTTP_request_handler.task_queue = task_queue
    serv = HTTP_server(("", 8080), HTTP_request_handler)
    worker_list.get_status_on_change()
    #generate ETag when init
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        pass

    finally:
        try:
            serv.shutdown()
            thread_pool.close()
            thread_pool.join()
        except KeyboardInterrupt:
            pass
        

