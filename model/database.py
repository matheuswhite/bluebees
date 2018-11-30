

class Storage:

    def __init__(self):
        self.__coll = {}

    def add(self, other):
        self.__coll[other.name] = other

    def delete(self, item_name):
        del self.__coll[item_name]

    def get_all(self):
        return self.__coll.values()

    def get(self, item_name):
        return self.__coll[item_name]

    def update_name(self, old_name, new_name):
        item = self.__coll[old_name]
        item.name = new_name
        self.delete(old_name)
        self.add(item)

    def exist(self, item_name):
        for k in self.__coll.keys():
            if k == item_name:
                return True
        return False


nets = Storage()
apps = Storage()
devices = Storage()
nodes = Storage()
