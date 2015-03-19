from curl_task import download_task, download_task_from_cmdline
import shlex

def do_request(s, queue):
    req = shlex.split(s)
    if req[0] == 'download':
        do_download(req[1:], queue)
    elif req[0] == 'curl':
        do_curl(req[1:], queue)
    else:
        return r'{0}: No such service. The leather club is two blocks down.'.format(s)
    return r'{0}: Fucking Slaves get your asses back here!'.format(req[0])

def do_download(download_param, queue):
    if len(download_param) == 1:
        filename = None
    else:
        filename = download_param[1]
    print('downloading to:', filename)
    queue.put(download_task(download_param[0], filename))

def do_curl(download_param, queue):
    print(download_param)
    queue.put(download_task_from_cmdline(download_param))
 