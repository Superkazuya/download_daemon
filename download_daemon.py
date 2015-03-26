from multiprocessing.pool import ThreadPool
from server import HTTP_request_handler, HTTP_server
from threading import Thread
from protocol import do_request
from events import event_list, summary
from task_collection import task_pending_queue
import cgitb


#dirty?
thread_num = 5

ADDR = ('', 8012)

class grunt:
    def __init__(self):
        self.task = None
        #atomic?
        while True:
            self.task = task_pending_queue.get()
            self.task.start()
            self.task = None
            task_pending_queue.task_done()


def apply_async_callback(arg):
    pass
    print(arg)

def apply_async_error_callback(arg):
    print("error", arg)
    pass
    
if __name__ == '__main__':
    thread_pool = ThreadPool(thread_num)
    for i in range(thread_num):
        thread_pool.apply_async(grunt, callback=apply_async_callback, error_callback=apply_async_error_callback)

    summary_generating_thread = Thread(target = summary.update_all)
    summary_generating_thread.start()
    event_list.garbage_collection()
    serv = HTTP_server(ADDR, HTTP_request_handler)
    serv.serve_forever()
    serv.shutdown()
    summary_generating_thread.join()
    thread_pool.close()
    thread_pool.join()
        

