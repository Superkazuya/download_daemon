import argparse
import events
from os import path, rename, remove
from task_collection import task_pending_queue, task_delayed_dict, existing_task_dict
from curl import another_curl_class

class task():
    event_list = events.event_list
    state_list = ['pending', 'paused', 'active', 'paused', 'complete', 'complete']
    #0: pending 1:paused while pending(delayed) 2:active 3:active but paused 4:canceled 5:finished 
    #one single class variable means there's only one receiving end(one event stream in sse)
    def task_init(self):
        self.identifier = hex(id(self))
        #task unique identifier
        #work with weakref to get object by id
        existing_task_dict[self.identifier] = self
        #weakref value dictionary

    def enter_pending_queue(self):
        self.state_change(0)
        task_pending_queue.put(self)

    def run(self):
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
        with task.event_list.lock:
            ev = events.task_event(ev_type, self)
            ev.data = data
            task.event_list.append(ev)
            #Thanks to GIL, if it's in the list, it's already readable. But the self.sentinel._prev node is probably still not changed?
            task.event_list.new_event.set()
            task.event_list.new_event.clear()

    def state_change(self, new_state):
        self.state = new_state
        self.generate_event('state', self.state_list[self.state])
        #convenient way to generate a state event

        
class download_task(task):
    def __init__(self, url, filename = None):
        self.task_init()
        self.finished, self.total = 0, 0
        self.url = url

        self.curl_config(filename)
        self.enter_pending_queue()
        #call this when the task is ready
        self.send_messages_when_ready()


    def curl_config(self, filename):
        self.c = another_curl_class()
        self.c.handle_name_input(filename)
        self.c.curl.setopt(self.c.curl.URL, self.url)
        self.c.curl.setopt(self.c.curl.FOLLOWLOCATION, True)
        self.c.curl.setopt(self.c.curl.MAXREDIRS, 5)
        self.c.curl.setopt(self.c.curl.NOPROGRESS, False)
        self.c.curl.setopt(self.c.curl.PROGRESSFUNCTION, self.progress)

        self.c.resume_callback = lambda:self.state_change(2)
        self.c.pause_callback = lambda:self.state_change(3)
        self.c.cancel_callback = lambda:self.state_change(4)
        self.c.complete_callback = lambda:self.state_change(5)
        self.c.remote_filename_callback = lambda x:self.generate_event('description', x)


    def send_messages_when_ready(self):
        #this should be sent after the task is enqueued
        if not self.c.use_remote_filename:
            self.generate_event('description', path.basename(self.c.fullname))

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
            print('pause error', self.state)
            
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
            print('resume error', self.state)

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
            print('cancel error', self.state)

    def start(self):
        #check those are canceled or paused. no state change here
        if self.state == 1:
            #paused, need to be put into task_delayed_dict
            task_delayed_dict[self.identifier] = self
            return
        elif self.state == 2 or self.state == 3 or self.state == 5:
            print('start error', self.state)
            return
        elif self.state == 4:
            #canceled while it was still in the task_pending_queue
            return

        self.state_change(2)
        #if state is pending
        self.c.download(self.url)
        #if self.c.curl.getinfo(self.c.curl.RESPONSE_CODE) != 200:
        #    print("response code: {0}".format(self.c.curl.RESPONSE_CODE))
        
    def progress(self, total_download, downloaded, total_upload, uploaded):
        #string = r"Downloading to {0} {1:.2f}/{2:.2f} ({3:.2f}%)"
        #try:
        #    percentage = 100*downloaded/total_download
        #    #print("\r", string.format(self.filename, downloaded, total_download, percentage), end='')
        #    print(string.format(self.filename, downloaded, total_download, percentage))
        #except ZeroDivisionError:
        #    print(self.filename, downloaded, total_download)
        self.c.in_progress_callback()
        
        if total_download > self.total:
           self.generate_event('size', total_download)
           self.total = total_download

        if not self.total == 0:
            if (downloaded - self.finished)*100 > total_download:
                #one percent progress is made
                self.generate_event('progress', downloaded)
                self.finished = downloaded

       
class download_task_from_cmdline(download_task):
    def __init__(self, *cmdline):
        self.task_init()

        parser = argparse.ArgumentParser()
        parser.add_argument('-H', '--header', action='append')
        parser.add_argument('-o', '--output', action='store')
        parser.add_argument('-L', '--location', action='store_true')
        parser.add_argument('-O', '--remote-name', action='store_true')
        parser.add_argument('url')
        args = parser.parse_known_args(cmdline)[0]

        if args.output:
            filename = args.output
        else:
            filename = None
        self.finished, self.total = 0, 0

        self.url = args.url
        self.curl_config(filename)

        self.c.curl.setopt(self.c.curl.FOLLOWLOCATION, args.location)
        self.c.curl.setopt(self.c.curl.HTTPHEADER, args.header)

        self.enter_pending_queue()
        #call this when the task is ready
        self.send_messages_when_ready()
