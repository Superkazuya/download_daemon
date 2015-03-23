import pycurl
import argparse
import events

class task():
    event_list = events.event_list
    #one single class variable means there's only one receiving end(event stream in sse)
    def __init__(self):
        self.state = 0
        self.finished_size = 0
        #0: pending 1:suspended 2:active (or probably finished)
        self.grunt = None
        #which grunt is doing the work?
        self.identifier = hex(id(self))
        #task unique identifier
        self.size_get = False
        self.last_event_id = 0
        self.generate_event('state', 'pending') 
        #this should probably be placed after the actual enqueuing ?
        
    def get_status(self):
        raise NotImplemented
    def get_progress(self):
        raise NotImplemented
    def on_complete(self):
        pass
        
    def generate_event(self, ev_type, data):
        #no retry?
        #reading from the event_list 
        #make sure they are ready when new connections read them
        with task.event_list.lock:
            ev = events.task_event(ev_type, self)
            self.last_event_id = ev.get_key();
            ev.data = data
            task.event_list.append(ev)
            #if it's in the list, it's already readable. But It's next node is probably None
        #return ev


class download_task(task):
    def __init__(self, url, write_to):
        self.url = url
        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.URL, url)
        self.curl.setopt(self.curl.FOLLOWLOCATION, True)
        self.curl.setopt(self.curl.MAXREDIRS, 5)
        self.curl.setopt(self.curl.NOPROGRESS, False)
        self.curl.setopt(self.curl.PROGRESSFUNCTION, self.progress)
        self.filename = write_to
        if self.filename:
            self.generate_event('description', self.filename)
        task.__init__(self)

    def start(self):
        if not self.filename:
            self.filename = 'test'
            #Need better strategy
            self.generate_event('description', self.filename) 

        with open(self.filename, 'wb') as fd:
            self.curl.setopt(self.curl.WRITEDATA, fd)

            print("Download {0} to ./{1}.".format(str(self.url), str(self.filename)))
            try:
                self.generate_event('state', 'active') 
                self.curl.perform()
                self.state = 2
                self.generate_event('state', 'complete') 
            except pycurl.error as e:
                self.generate_event('error', 'unable to start') 
                
            if self.curl.getinfo(self.curl.RESPONSE_CODE) != 200:
                print("response code: {0}".format(self.curl.RESPONSE_CODE))
        self.curl.close()

    def get_status(self):
        return ' > Downloading {0}'.format(self.filename)
        
    def pause(self):
        try:
            self.curl.pause(self.curl.PAUSE_RECV)
            self.state = 1
        except pycurl.error as e:
            self.generate_event('error', 'unable to pause') 

    def resume(self):
        try:
            self.curl.pause(self.curl.PAUSE_CONT)
            self.state = 2
        except pycurl.error as e:
            self.generate_event('error', 'unable to resume') 

    def get_size(self):
        if self.total > 0.01 and not self.size_sent:
            self.generate_event('size', self.total)
            self.size_sent = True

    def progress(self, total_download, downloaded, total_upload, uploaded):
        #string = r"Downloading to {0} {1:.2f}/{2:.2f} ({3:.2f}%)"
        #try:
        #    percentage = 100*downloaded/total_download
        #    print("\r", string.format(self.filename, downloaded, total_download, percentage), end='')
        #except ZeroDivisionError:
        #    pass
        if self.size_get:
            if (downloaded - self.finished_size)*100 > total_download:
                #one percent progress is made
                self.generate_event('progress', downloaded)
                self.finished_size = downloaded

        elif total_download > 0.01:
            #self.generate_event('size', total_download)
            self.size_get = True
            self.generate_event('size', total_download)
        
    def get_progress(self):
        return [int(self.finished), int(self.total)]

 
class download_task_from_cmdline(download_task):
    def __init__(self, cmdline):
        parser = argparse.ArgumentParser()
        parser.add_argument('-H', '--header', action='append')
        parser.add_argument('-o', '--output', action='store')
        parser.add_argument('-L', '--location', action='store_true')
        parser.add_argument('-O', '--remote-name', action='store_true')
        parser.add_argument('url')
        task.__init__(self)
        args = parser.parse_known_args(cmdline)[0]

        self.url = args.url
        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.URL, self.url)
        self.curl.setopt(self.curl.MAXREDIRS, 5)
        self.curl.setopt(self.curl.NOPROGRESS, False)
        self.curl.setopt(self.curl.PROGRESSFUNCTION, self.progress)

        self.curl.setopt(self.curl.FOLLOWLOCATION, args.location)
        if args.output:
            self.filename = args.output
            self.generate_event('description', self.filename)
        else:
            self.filename = None
        self.curl.setopt(self.curl.HTTPHEADER, args.header)
        
        
