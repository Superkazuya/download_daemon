from threading import Lock
from tasks import task

class snapshot(dict):
    #generate snapshots using the event_list
    #there's only one snapshot instance.
    #in the update process, we need to simulate task.js behaviors
    def __init__(self, *args, **kwargs):
        self.newest_ev_node = task.event_list.sentinel
        dict.__init__(self, *args, **kwargs)
        self.mutexlock = Lock()
        #lock to sync with new_connection
        #so new connections could block without affecting others
        #It's still possible to block all new connections forever though

    #key = task.identifier
    def update(self, new_ev_node):
        self.newest_ev_node = new_ev_node;
        if(new_ev_node.ev_type == 'state'):
           if(new_ev_node.data == 'complete'):
            #need to delete this item from the snapshot
                del self[new_ev_node.task.identifier] 
                return
           elif(new_ev_node.data == 'pending'):
               #init a new task
                self[new_ev_node.task.identifier] = {'state': 'pending'}
                return

        self[new_ev_node.task.identifier][new_ev_node.ev_type] = new_ev_node.data

    def update_all(self):
        #todo plz no blocking spamerino
        while True:
            while not self.newest_ev_node._next is task.event_list.sentinel:
                #new node available
                with self.mutexlock:
                    self.update(self.newest_ev_node._next)
        
summary = snapshot()

 
