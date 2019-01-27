from core.dongle import dongle_driver
from core.scheduling import Task, scheduler

class NodeCache:

    def __init__(self, node_id: int):
        self.id = node_id
        self.send_queue = []
        self.recv_queue = []

    def get(self):
        if len(self.recv_queue) == 0:
            return None

        msg = self.recv_queue[0]
        self.recv_queue = self.recv_queue[1:]
        return msg

    def put(self, message: bytes):
        self.send_queue.append(message)

class MessageGate:

    def __init__(self):
        self.node_caches = {}
        self.driver = dongle_driver
        self.is_alive = True

        self.message_gate_task = scheduler.spawn_task(self._message_gate_run_t)

    def _message_gate_run_t(self, self_task: Task):
        while self.is_alive:
            msg = None
            while msg is None:
                msg = dongle_driver.recv('message')
                yield
                for k in list(self.node_caches.keys()):
                    if len(self.node_caches[k].send_queue) > 0:
                        msg = self.node_caches[k].send_queue[0]
                        self.node_caches[k].send_queue = self.node_caches[k].send_queue[1:]
                        self.driver.send(2, 20, msg)
                        yield
            
            for k in list(self.node_caches.keys()):
                self.node_caches[k].recv_queue.append(msg)

    def register_node(self, node_id: int):
        self.node_caches[node_id] = NodeCache(node_id)
    
    def put_message(self, node_id: int, message: bytes):
        self.node_caches[node_id].put(message)

    def retrive_message(self, node_id: int):
        self.node_caches[node_id].get()

message_gate = MessageGate()
