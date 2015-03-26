import pycurl 
import os, re
import uuid 

class another_curl_class():
    def __init__(self):
        self.curl = pycurl.Curl()
        self.headers = {}
        self.use_remote_filename = False
        self.remote_filename = None
        self.fullname = None
        self.cancel = False
        self.pause = False

    def handle_name_input(self, filename):
        if filename == None:
            filename = ""
        filename = os.path.abspath(filename.strip())
        #if you want a file name that is identical to a directory, you probably need to change it manually
        if os.path.isdir(filename):
            self.use_remote_filename = True
            self.path = filename

            self.name = str(uuid.uuid4())
            #placeholder name
            while os.path.exists(self.path+'/'+self.name):
                self.name = str(uuid.uuid4())
            self.fullname = self.path+'/'+self.name
            #could have duplicated '/'
        elif os.path.exists(filename):
            self.fullname = filename
            print('already exists. overwrite boys')
        else:
            self.fullname = filename

 
    def download(self, url):
        self.effective_url = url
        if self.use_remote_filename:
            self.curl.setopt(self.curl.HEADERFUNCTION, self.header_function)
            #or override this using your own callback
        with open(self.fullname, 'wb') as f:
            self.curl.setopt(self.curl.WRITEDATA, f)
            self.curl.setopt(self.curl.WRITEFUNCTION, lambda x: -1 if self.cancel else f.write(x))

            try:
                self.curl.perform()
            except pycurl.error as e:
                #we need to cancel it anyway
                if not self.cancel:
                    self.error_callback(e)

                self.cancel_callback()
                self.cancel_cleanup()
            else:
                self.complete_callback()
                self.apply_remote_name()
            finally:
                self.curl.close()

    def complete_callback(self):
        pass

    def apply_remote_name(self):
        if(self.use_remote_filename):
            print('trying to rename', self.path+'/'+self.remote_filename)
            os.rename(self.fullname, self.path+'/'+self.remote_filename)
    def cancel_cleanup(self):
        if os.path.exists(self.fullname):
            os.remove(self.fullname)

    def cancel_callback(self):
        pass

    def do_cancel(self):
        #cancel is irreversible
        if self.cancel:
            print('cancel error: already canceled.')
        else:
            self.cancel = True

    def pause_callback(self):
        pass
    def do_pause(self):
        if self.cancel:
            print('pause error: already canceled.')
            return
        elif self.pause:
            print('pause error: already paused.')
            return

        self.pause = True

    def resume_callback(self):
        pass

    def do_resume(self):
        if self.cancel:
            print('resume error: already canceled.')
            return
        elif not self.pause:
            print('resume error: not paused.')
            return
        self.pause = False

    def in_progress_callback(self):
        #place this in the progress callback
        if self.cancel:
            self.pause = False
            self.curl.pause(self.curl.PAUSE_CONT)
            
        elif self.pause:
            self.curl.pause(self.curl.PAUSE_RECV)
            self.pause_callback()
        else:
            self.curl.pause(self.curl.PAUSE_CONT)
            self.resume_callback()
                
    def header_function(self, raw_headline):
        if(self.remote_filename != None or not self.use_remote_filename):
            return
        raw_headline = raw_headline.decode('utf-8').strip()
        #raw_headline = raw_headline.decode('iso-8859-1').strip()
        #print('http header >>>', raw_headline)
        if not raw_headline:
            #end of header
            if 'content-disposition' in self.headers:
                pattern = 'filename=([\'\"])(?P<filename>.*?)\\1$'
                self.remote_filename = re.search(pattern, self.headers['content-disposition']).group('filename')
            if 'location' in self.headers:
                self.effective_url = self.headers['location']
            elif self.remote_filename == None:
                li = self.effective_url.strip().split(r'/')
                for i in li:
                    if i:
                        self.remote_filename = i
            self.headers.clear()
            if self.remote_filename:
                #you get the remote name! congratulations
                self.remote_filename_callback(self.remote_filename)
                print('using remote name:', self.remote_filename)
        elif ':' in raw_headline:
            name, value = raw_headline.split(':', 1)
            name = name.strip().lower()
            value = value.strip()
            self.headers[name] = value

    def remote_filename_callback(self, remote_filename):
        pass

    def error_callback(self, error):
        pass
