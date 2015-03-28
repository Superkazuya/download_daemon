import argparse
from os import path
from task_collection import task_pending_queue, task_delayed_dict, existing_task_dict
from events import event_list, task_event
from curl import another_curl_class
import logging

class task():
    state_list = ['pending', 'paused', 'active', 'paused', 'complete', 'complete']
    #0: pending 1:paused while pending(delayed) 2:active 3:active but paused 4:canceled 5:finished 
    def task_init(self):
        self.identifier = hex(id(self))
        #task unique identifier
        #work with weakref to get object by id
        existing_task_dict[self.identifier] = self
        #weakref value dictionary
        #used when you want to control the task by it's identifier

    def enter_pending_queue(self):
        self.state_change(0)
        task_pending_queue.put(self)

    def start(self):
        raise NotImplemented
    def pause(self):
        raise NotImplemented
    def resume(self):
        raise NotImplemented
    def cancel(self):
        raise NotImplemented
        
    def generate_event(self, ev_type, data):
        #generate an event and append it to the end of the event_list
        #use mutex lock to guarantee the event_ids are in ascending order
        with event_list.lock:
            ev = task_event(ev_type, self)
            ev.data = data
            event_list.append(ev)
            #if it's in the list, it's already readable.
            #because the last meaningful bytecode is STORE_ATTR(_prev) in linked_list append() method
            event_list.new_event.set()
            event_list.new_event.clear()
        logging.debug('new event task: %s', ev.to_dict())

    def state_change(self, new_state):
        self.state = new_state
        self.generate_event('state', self.state_list[self.state])
        #convenient way to generate a state event

        
class download_task(task):
    def __init__(self, list_args):
        #don't override __init__() if possible
        self.task_init()

        self.curl_config(list_args)
        self.set_curl_callbacks()
        self.enter_pending_queue()
        #call this when the task is ready,


    def curl_config(self, list_args):
        dct = {'location':True, 'url':list_args[0]}

        try:
            dct['output'] = list_args[1]
        except IndexError:
            logging.debug('no output option specified.')
            
        self.c = another_curl_class(**dct)


    def set_curl_callbacks(self):
        if not self.c.use_remote_filename:
            logging.info('using specified name')
            self.generate_event('description', '{1} >>> {0}'.format(*path.split(self.c.get_fullpath())))
            #this is saaaaaaaaaaaaaad

        self.c.resume_callback = lambda:self.state_change(2)
        self.c.pause_callback = lambda:self.state_change(3)
        self.c.cancel_callback = lambda:self.state_change(4)
        self.c.complete_callback = lambda:self.state_change(5)
        #self.c.local_filename_callback = lambda x:self.generate_event('description', '{1} >>> {0}'.format(*path.split(x)))
        #this callback will be called before the init of c finishes. So it will never be called. S A D B O Y S
        self.c.remote_filename_callback = lambda x:self.generate_event('description', '{1} >>> {0}'.format(*path.split(x)))
        self.c.error_callback = self.error_cb

        self.finished, self.total = 0, 0
        self.c.progress_callback = self.progress

    def pause(self):
        #cannot pause when activated 
        if self.state == 0:
            #pending
            self.state_change(1)
        elif self.state == 2:
            self.c.do_pause()
            #will be handled by curl.py
            #callback will be called when the state change is done successfully
        else:
            logging.error('pause error: state %d', self.state)
            
    def resume(self):
        if self.state == 1:
            #previously pending
            if self.identifier in task_delayed_dict:
                del task_delayed_dict[self.identifier]
                self.enter_pending_queue()
            else:
                self.state_change(0)
        elif self.state == 3:
            self.c.do_resume()
        else:
            logging.error('resume error: state %d', self.state)

    def cancel(self):
        if self.state == 0:
            self.state_change(4)
        elif self.state == 1:
            if self.identifier in task_delayed_dict:
                del task_delayed_dict[self.identifier]
            self.state_change(4)
        elif self.state == 2 or self.state == 3:
            self.c.do_cancel()
        else:
            logging.error('cancel error: state %d', self.state)

    def start(self):
        #check those are canceled or paused. no state change here
        if self.state == 1:
            #paused, need to be put into task_delayed_dict
            task_delayed_dict[self.identifier] = self
            return
        elif self.state == 2 or self.state == 3 or self.state == 5:
            logging.error('start error: state %d', self.state)
            return
        elif self.state == 4:
            #canceled while it was still in the task_pending_queue
            return

        self.state_change(2)
        #if state is pending
        self.c.download()
        
    def progress(self, total_download, downloaded, total_upload, uploaded):
        if total_download > self.total:
           self.generate_event('size', total_download)
           self.total = total_download

        if not self.total == 0:
            if (downloaded - self.finished)*100 > total_download:
                #one percent progress is made
                self.generate_event('progress', downloaded)
                self.finished = downloaded

    def error_cb(self, msg):
        if self.c.remote_filename:
            self.generate_event('error', self.c.remote_filename+' canceled due to error '+str(msg)) 
        else:
            self.generate_event('error', self.c.basename +' ('+self.c.url+') canceled due to error '+str(msg))


       
class download_task_from_cmdline(download_task):
    def curl_config(self, list_args):
        parser = argparse.ArgumentParser()
        parser.add_argument('-H', '--header', action='append')
        parser.add_argument('-o', '--output', action='store')
        parser.add_argument('-L', '--location', action='store_true')
        parser.add_argument('-O', '--remote-name', action='store_true')
        parser.add_argument('-J', '--remote-header-name', action='store_true')
        parser.add_argument('url')
        args = parser.parse_known_args(list_args)[0]

        self.c = another_curl_class(**vars(args))
