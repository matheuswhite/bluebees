#!/usr/bin/python3
from threading import Lock
import random


# TODO: Change list for other data structure
class SharedIDPool:

    def __init__(self, max_size):
        self.max_size = max_size
        self.dirty_ids = []
        self.dirty_ids_size = max_size
        self.lock = Lock()

    def get_new_id(self):
        self.lock.acquire()

        if len(self.dirty_ids) == self.dirty_ids_size:
            self.dirty_ids.clear()

        id_ = random.randrange(0, self.max_size)
        while id_ in self.dirty_ids:
            id_ = random.randrange(0, self.max_size)

        self.dirty_ids.append(id_)
        self.lock.release()
        return id_
