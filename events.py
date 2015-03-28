import datetime
from threading import Lock, Event, Timer
from weakref import WeakValueDictionary

class list_node:
    def __init__(self):
        self.event_id = '0'
        self._next = None 

    def get_key(self):
        raise NotImplemented

    def __equal__(self, other):
        return self.event_id == other.event_id

    def __lt__(self, other):
        return self.event_id < other.event_id

    def __le__(self, other):
        return self.event_id <= other.event_id

    def __gt__(self, other):
        return self.event_id > other.event_id

    def __ge__(self, other):
        return self.event_id >= other.event_id

    def __ne__(self, other):
        return (not self==other)


class event(list_node):
    def __init__(self, ev_type):
        list_node.__init__(self)
        self.event_id = self.generate_id()
        self.ev_type = ev_type

    def get_key(self):
        return self.event_id

    def generate_id(self):
        t = datetime.datetime.now()
        t = t - datetime.datetime(2015, 3, 14)
        t /= datetime.timedelta(microseconds=1)
        return hex(int(t))[2:]

class task_event(event):
    #These events will be checked by the server and dispatched to clients.
    def __init__(self, ev_type, task):
        event.__init__(self, ev_type)
        self.task = task
        #owner
    def to_dict(self):
        return {self.task.identifier: {self.ev_type: self.data}}

class linked_list:
    def __init__(self):
        self.sentinel = list_node()
        self.sentinel._prev = self.sentinel
        self.sentinel._next = self.sentinel
        self.count = 0

    def append(self, new_node):
        new_node._next = self.sentinel
        self.sentinel._prev._next = new_node
        self.count += 1
        self.sentinel._prev = new_node

    def popleft(self):
       #remove old entries
       if self.sentinel._next == self.sentinel:
           raise IndexError
       r = self.sentinel._next
       self.sentinel._next = self.sentinel._next._next
       self.count -= 1
       del r
       #return r

    def __getitem__(self, key):
        node = self.sentinel._next
        while not node == self.sentinel:
            if node.get_key() == key:
                return node
            elif node.get_key() < key:
                node = node._next
            else:
                raise KeyError
        raise KeyError

       
class event_linked_list(linked_list):
    #an event list stores events generated by tasks(task_event instances). 
    #the server will try to find new events for the clients by event_ids
    #old and unreferenced entries should be cleaned, probably in a lazy manner
    #!!!need to explicitly guarantee thread safety and the event_ids are in ascending order
    def __init__(self):
        linked_list.__init__(self)
        self.sentinel.event_id = '0'
        self.lock = Lock()
        self.new_event = Event()
        self.users = WeakValueDictionary()

    def garbage_collection(self):
        #if not self.sentinel._next is self.sentinel:
        if not (self.sentinel._next is self.sentinel or self.sentinel._next._next is self.sentinel):
            #nothing to clean, or only one node is left
            oldest_node_to_keep = self.sentinel._prev

            with summary.mutexlock:
                for id, user in self.users.items():
                    if user.newest_ev_node < oldest_node_to_keep:
                        oldest_node_to_keep = user.newest_ev_node

            c = 0
            while self.sentinel._next < oldest_node_to_keep and not self.sentinel._next is self.sentinel:
                print('remove >', self.sentinel._next.to_dict(), 'its next is', self.sentinel._next._next.to_dict())
                self.popleft()
                c += 1

            print('-'*40)
            print("cleaning... the oldest event in the list is now", self.sentinel._next.event_id)
            print("the newes event in the list is now", self.sentinel._prev.event_id)
            print(c, 'node(s) have been cleaned.', self.count, 'node(s) left')
        gc = Timer(20, self.garbage_collection)
        gc.start()

    #def newest_nodes_ref(self, event_id):
    #    #node of event_id reference +1, by one of the readers(server threads, or the snapshot thread)
    #    if event_id in self.newest_nodes:
    #        self.newest_nodes[event_id] += 1
    #    else:
    #        self.newest_nodes[event_id] = 1

    #def newest_nodes_unref(self, event_id):
    #    if self.newest_nodes[event_id] == 1:
    #        del self.newest_nodes[event_id]
    #    else:
    #        self.newest_nodes[event_id] -= 1


event_list = event_linked_list()

class snapshot(dict):
    #generate snapshots using the event_list
    #there's only one snapshot instance.
    #in the update process, we need to simulate task.js behaviors
    def __init__(self, *args, **kwargs):
        self.newest_ev_node = event_list.sentinel
        dict.__init__(self, *args, **kwargs)
        self.mutexlock = Lock()
        #lock to sync with new_connection
        #so new connections could block without affecting others
        #It's still possible to block all new connections forever though
        event_list.users[id(self)] = self
        #won't need to delete itself

    #key = task.identifier
    def update(self, new_ev_node):
        self.newest_ev_node = new_ev_node;
        #print('trying to update the snapshot with', new_ev_node.to_dict())
        if(new_ev_node.ev_type == 'state'):
           if(new_ev_node.data == 'complete'):
            #need to delete this item from the snapshot
                del self[new_ev_node.task.identifier] 
                return
           elif(new_ev_node.data == 'pending'):
               #init a new task
                self[new_ev_node.task.identifier] = {'state': 'pending'}
                return

        try:
            self[new_ev_node.task.identifier][new_ev_node.ev_type] = new_ev_node.data
        except Exception:
            print("-"*20, "update error", "-"*20)
            print(new_ev_node.task.identifier, new_ev_node.ev_type, new_ev_node.data)
            print('-'*45)
            raise 

    def update_all(self):
        #todo plz no blocking spamerino
        while True:
            if self.newest_ev_node._next is event_list.sentinel:
                event_list.new_event.wait(5)
                #new node available
            else:
                with self.mutexlock:
                    #this will block a new connection
                    self.update(self.newest_ev_node._next)
        
summary = snapshot()

 
