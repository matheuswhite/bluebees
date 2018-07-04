#!/usr/bin/python3
from queue import Queue
from threading import Lock
import random


# TODO: Change queue for other data structure
# TODO: Add a unit test to this class
class SharedIDPool:

    def __init__(self, max_size):
        self.max_size = max_size
        self.dirty_ids = Queue(max_size)
        self.lock = Lock()

    def get_new_id(self):
        self.lock.acquire()

        if self.dirty_ids.full():
            self.dirty_ids = Queue()

        dirty_ids = iter(self.dirty_ids.get_nowait())

        id_ = random.randrange(0, self.max_size)
        while id_ in dirty_ids:
            id_ = random.randrange(0, self.max_size)

        self.dirty_ids.put_nowait(id_)
        self.lock.release()
        return id_
