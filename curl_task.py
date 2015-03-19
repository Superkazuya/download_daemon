import pycurl
import argparse

class task():
    def __init__(self):
        self.finished = 0;
        self.total = 0;
    def get_status(self):
        raise NotImplemented
    def get_progress(self):
        raise NotImplemented

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
        task.__init__(self)

    def start(self):
        if not self.filename:
            self.filename = 'test'
            #Need better strategy

        with open(self.filename, 'wb') as fd:
            self.curl.setopt(self.curl.WRITEDATA, fd)

            print("Download {0} to ./{1}.".format(str(self.url), str(self.filename)))
            self.curl.perform()
            if self.curl.getinfo(self.curl.RESPONSE_CODE) != 200:
                print("response code: {0}".format(self.curl.RESPONSE_CODE))
        self.curl.close()

    def get_status(self):
        return ' > Downloading {0}'.format(self.filename)
        
    def pause(self):
        self.curl.pause(self.curl.PAUSE_RECV)

    def resume(self):
        self.curl.pause(self.curl.PAUSE_CONT)

    def progress(self, total_download, downloaded, total_upload, uploaded):
        string = "\rDownloading to {0} {1:.2f}/{2:.2f} ({3:.2f}%)"
        try:
            percentage = 100*downloaded/total_download
            print(string.format(self.filename, downloaded, total_download, percentage), end='')
        except ZeroDivisionError:
            pass
        self.finished, self.total= downloaded, total_download

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
        else:
            self.filename = None
        self.curl.setopt(self.curl.HTTPHEADER, args.header)
        
        
