

class Storage:

    def __init__(self):
        self.__list = {}

    def add(self, element):
        self.__list[element.name] = element

    def get_all(self):
        return self.__list.values()

    def get(self, index):
        return self.__list[index]

    def update_name(self, index, new_element):
        element = self.__list[index]
        element.name = new_element
        del self.__list[index]
        self.add(element)


nets = Storage()
apps = Storage()
devices = Storage()
nodes = Storage()
