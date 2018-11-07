

class SimpleCache:

    def __init__(self):
        self.__queue = []

    def push(self, item):
        if item not in self.__queue:
            self.__queue.append(item)
            return True
        return False

    def pop(self):
        if len(self.__queue) > 0:
            item = self.__queue[0]
            self.__queue = self.__queue[1:]
            return item
        return None

    def seek(self):
        if len(self.__queue) > 0:
            return self.__queue[0]
        return None

    def clear_all(self):
        self.__queue = []

    def __len__(self):
        return len(self.__queue)

    def __str__(self):
        return str(self.__queue)

class DongleCache:

    def __init__(self):
        self.adv_cache = SimpleCache()
        self.beacon_cache = SimpleCache()
        self.message_cache = SimpleCache()
        self.prov_cache = SimpleCache()

    def __getitem__(self, item: str):
        if item == 'beacon':
            return self.beacon_cache
        elif item == 'message':
            return self.message_cache
        elif item == 'prov':
            return self.prov_cache
        elif item == 'adv':
            return self.adv_cache
        else:
            return None
