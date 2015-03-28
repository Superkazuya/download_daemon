from tasks import download_task, download_task_from_cmdline
import shlex

def do_request(s):
    req = shlex.split(s)
    if len(req) < 1:
        return r'{0}: No such service. The leather club is two blocks down.'.format(s)
    if req[0] == 'download':
        if len(req) < 2:
            return r'{0}: at least two args'.format(s)
        do_download(req[1:])
    elif req[0] == 'curl':
        do_curl(req[1:])
    else:
        return r'{0}: No such service. The leather club is two blocks down.'.format(s)
    return None

def do_download(download_param):
    download_task(download_param)
    #pass directly as a list

def do_curl(download_param):
    download_task_from_cmdline(download_param)
 
