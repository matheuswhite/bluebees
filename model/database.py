

class Storage:

    def __init__(self):
        self.__list = []

    def add(self, element):
        self.__list.append(element)

    def get_all(self):
        return self.__list

    def update_component(self, index):
        raise NotImplementedError


nets = Storage()
apps = Storage()
devices = Storage()
nodes = Storage()
