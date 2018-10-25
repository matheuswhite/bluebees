

class SimpleQueue:

    def __init__(self):
        self.__queue = []

    def push(self, item):
        self.__queue.append(item)

    def pop(self):
        if len(self.__queue) > 0:
            item = self.__queue[0]
            self.__queue = self.__queue[:-1]

class DongleCache:

    def __init__(self):
        self.adv_queue =