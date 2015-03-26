from queue import Queue
from weakref import WeakValueDictionary

task_pending_queue = Queue()
existing_task_dict = WeakValueDictionary()

task_delayed_dict = {}
#stores tasks that are paused while pending. Need to store them there so they won't be GC'ed

