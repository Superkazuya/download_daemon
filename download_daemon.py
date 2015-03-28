from multiprocessing.pool import ThreadPool
from server import HTTP_request_handler, HTTP_server
from threading import Thread
from protocol import do_request
from events import event_list, summary
from task_collection import task_pending_queue
import logging


#dirty?
thread_num = 5

ADDR = ('', 8012)

class grunt:
    def __init__(self):
        self.task = None
        #atomic?
        while True:
            self.task = task_pending_queue.get()
            try:
                self.task.start()
            except Exception as e:
                #catch all error so this grunt won't hang
                self.task.state_change(4)
                self.task.generate_event('error', str(e))

                logging.exception("-"*40)
                logging.exception("our grunt reported an error.")
                logging.exception(str(e))
                logging.exception("-"*40)

            self.task = None
            task_pending_queue.task_done()


def apply_async_error_callback(arg):
    logging.error("-"*40)
    logging.error("async_error_callback")
    logging.error(arg)
    logging.error("-"*40)
    
if __name__ == '__main__':
    logging.basicConfig()
    thread_pool = ThreadPool(thread_num)
    for i in range(thread_num):
        thread_pool.apply_async(grunt, error_callback=apply_async_error_callback)

    summary_generating_thread = Thread(target = summary.update_all)
    summary_generating_thread.start()
    event_list.garbage_collection()

    try:
        serv = HTTP_server(ADDR, HTTP_request_handler)
        serv.serve_forever()
    except KeyboardInterrupt:
        serv.shutdown()
        summary_generating_thread.join()
        thread_pool.close()
        thread_pool.join()


