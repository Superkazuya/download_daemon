from tasks import download_task, download_task_from_cmdline
from task_collection import existing_task_dict
import shlex

class form:
    @classmethod
    def process(cls, form_input):
        for key in form_input:
            if hasattr(cls, 'do_'+key):
                return getattr(cls, 'do_'+key)(form_input[key][0])
            elif key in ['pause', 'resume', 'cancel']:
                getattr(existing_task_dict[form_input[key][0]], key)()

    @staticmethod
    def do_request(r_body):
        count = 0
        ret_str = ''
        for l in r_body.splitlines():
            l = l.strip()
            if not l:
                continue
            ret = service.process(l)
            if ret:
                ret_str += ret+'\n'
            else:
                count += 1

        if count == 1:
            ret_str += '1 request handled successfully.\n'
        elif count > 1:
            ret_str += '{0} request handled successfully.\n'.format(self.count)

        return ret_str 
                
            

class service:
    @classmethod
    def process(cls, request):
        req = shlex.split(request)
        if len(req) < 2:
            return r'{0}: at least two args! fuck you leather man.\n'.format(req)
        if hasattr(cls, 'do_'+req[0]):
            getattr(cls, 'do_'+req[0])(req[1:])
        else:
            return r'{0}: No such service. The leather club is two blocks down.\n'.format(req)
        

    @staticmethod
    def do_download(download_param):
        download_task(download_param)

    @staticmethod
    def do_curl(download_param):
        download_task_from_cmdline(download_param)

