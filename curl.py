import pycurl 
import os, re
import uuid 
from urllib import parse
import logging

class another_curl_class():
    arg_list = ['header', 'output', 'location', 'remote_name', 'remote_name_header', 'resume_callback', 'pause_callback', 'cancel_callback', 'complete_callback',
                'local_filename_callback', 'remote_filename_callback', 'error_callback', 'progress_callback']
    def __init__(self, **kwargs):
        self.curl = pycurl.Curl()
        self.headers_received = {}


        #pycurl options
        self.header = []
        self.output = None
        self.location = False
        self.remote_name = False
        self.remote_name_header = False
        
        for arg in self.arg_list:
            try:
                setattr(self, arg, kwargs[arg])
            except KeyError:
                pass

        try:
            #usually this will be handled during the argument parsing phase
            self.url = kwargs['url']
        except KeyError:
            logging.exception('no url? kappa')
            #self.error_callback('no url provided')
            raise


        self.use_remote_filename = self.remote_name or self.remote_name_header
        #not a libcurl option, need to implement it explicitly
        self.remote_filename = None

        self.path = os.path.abspath(os.path.expanduser("~/Locker Room"))
        self.basename = ""

        self.handle_name()
        self.do_curl_config()

        self.cancel = False
        self.paused = False
        self.action = 0
        #0 nothing, #1 pause #2 resume

    def do_curl_config(self):
        self.curl.setopt(self.curl.URL, self.url)
        self.curl.setopt(self.curl.FOLLOWLOCATION, self.location)
        self.curl.setopt(self.curl.MAXREDIRS, 5)

        #for pause/resume control, progress callback has to be enabled
        self.curl.setopt(self.curl.NOPROGRESS, False)
        self.curl.setopt(self.curl.PROGRESSFUNCTION, self.__the_one_and_the_only_real_progress_callback)

        self.curl.setopt(self.curl.HTTPHEADER, self.header)

        if self.use_remote_filename:
            #make it like the progress callback when it's necessary
            self.effective_url = self.url
            self.curl.setopt(self.curl.HEADERFUNCTION, self.in_header_callback)

    def get_fullpath(self):
        return os.path.abspath(self.path + '/'+self.basename)

    def handle_name(self):
        """mechanism: if use_remote_filename is set, 'output' will be treated as a directory to put the file in.
        else it's a file name(probably with path)
        if both use_remote_filename and output are unset, automatically set use_remote_filename to be True

        :returns: 
        :rtype: 

        """
        if (not self.use_remote_filename) and self.output == None:
            self.use_remote_filename = True

        if self.use_remote_filename:
            if not self.output == None:
                self.path = os.path.abspath(os.path.expanduser(self.output))
            self.basename = str(uuid.uuid4())
            #placeholder name
            while os.path.exists(self.get_fullpath()):
                self.basename = str(uuid.uuid4())

        else:
            #not using remote name
            self.path, self.basename = os.path.split(os.path.abspath(os.path.expanduser(self.output)))
            self.basename = self.basename.strip()
            self.local_filename_callback(self.get_fullpath())

        if os.path.exists(self.get_fullpath()):
            logging.warning(self.get_fullpath()+' exists. overwrite boys')
                
        try:
            os.makedirs(self.path)
        except OSError:
            #forgiveness
            pass

 
    def download(self):
            #or override this using your own callback
        with open(self.get_fullpath(), 'wb') as f:
            self.curl.setopt(self.curl.WRITEDATA, f)
            self.curl.setopt(self.curl.WRITEFUNCTION, lambda x: -1 if self.cancel else f.write(x))

            try:
                self.curl.perform()
            except pycurl.error as e:
                #we need to cancel it anyway
                if not self.cancel:
                    self.error_callback('in download '+str(e))

                self.cancel_callback()
                self.cancel_cleanup()
            else:
                self.complete_callback()
                self.apply_remote_name()
            finally:
                self.curl.close()


    def apply_remote_name(self):
        if(self.use_remote_filename):
            logging.info('trying to rename %s', os.path.abspath(self.path+'/'+self.remote_filename))
            fullname = os.path.abspath(self.path+'/'+self.remote_filename)
            if os.path.exists(fullname):
                logging.warning('%s already exists. overwrite boys', fullname)
            os.rename(self.get_fullpath(), fullname)
            #TODO if there's already a file with the same name, rename it 

    def cancel_cleanup(self):
        #TODO probably should clean the directories created as well?
        try:
            os.remove(self.get_fullpath())
        except OSError as e:
            if os.path.exists(self.get_fullpath()):
                logging.exception('cannot remove %s, is it a drectory?', self.get_fullpath())
                self.error_callback('in cancel_cleanup '+ str(e))

    def do_cancel(self):
        #cancel is irreversible
        if self.cancel:
            logging.info('cancel error: already canceled.')
        else:
            self.cancel = True

    def do_pause(self):
        if self.cancel:
            logging.info('pause error: already canceled.')
        elif self.paused:
            logging.info('pause error: already paused.')
        elif self.action:
            logging.info('pause error: There\'s already an action.')
        else:
            self.action = 1


    def do_resume(self):
        if self.cancel:
            logging.info('resume error: already canceled.')
        elif not self.paused:
            logging.info('resume error: not paused.')
        elif self.action:
            logging.info('resume error: There\'s already an action.')
        else:
            self.action = 2

    def in_progress_callback(self):
        if self.cancel:
            self.action = 0
            self.curl.pause(self.curl.PAUSE_CONT)
            self.paused = False
            
        elif not self.paused:
            if self.action == 1:
                self.curl.pause(self.curl.PAUSE_RECV)
                self.pause_callback()
                self.action = 0

        elif self.action == 2: 
            self.curl.pause(self.curl.PAUSE_CONT)
            self.resume_callback()
            self.action = 0

    def __the_one_and_the_only_real_progress_callback(self, *args, **kwargs):
        self.in_progress_callback()
        self.progress_callback(*args, **kwargs)
        
                
    def in_header_callback(self, raw_headline):
        #if(self.remote_filename != None or not self.use_remote_filename):
        if not self.remote_filename == None:
            return
        raw_headline = raw_headline.decode('utf-8').strip()
        #raw_headline = raw_headline.decode('iso-8859-1').strip()
        if not raw_headline:
            #end of header
            if 'content-disposition' in self.headers_received:
                pattern = 'filename=([\'\"])(?P<filename>.*?)\\1$'
                self.remote_filename = re.search(pattern, self.headers_received['content-disposition']).group('filename')
            if 'location' in self.headers_received:
                self.effective_url = self.headers_received['location']
            elif self.remote_filename == None:
                #if cannot redirect to anywhere and still doesn't get the name
                #what if the max redirect is reached????????????
                li = self.effective_url.strip().split(r'/')
                for i in li:
                    if i:
                        self.remote_filename = i
                tmp = ""
                while not self.remote_filename == tmp:
                    tmp, self.remote_filename = self.remote_filename, parse.unquote_plus(self.remote_filename)
                logging.info('We are using the last part of the effective url as file name.')
                #out of url encoding
            self.headers_received.clear()
            if self.remote_filename:
                #you get the remote name! congratulations
                self.remote_filename_callback(os.path.abspath(self.path+'/'+self.remote_filename))
                logging.info('using remote name: %s', self.remote_filename)
        elif ':' in raw_headline:
            name, value = raw_headline.split(':', 1)
            name = name.strip().lower()
            value = value.strip()
            self.headers_received[name] = value

    def local_filename_callback(self, filename):
        pass

    def remote_filename_callback(self, remote_filename):
        pass

    def error_callback(self, error):
        pass

    def progress_callback(self, *args, **kwargs):
        pass

    def complete_callback(self):
        pass

    def resume_callback(self):
        pass

    def pause_callback(self):
        pass

    def cancel_callback(self):
        pass
