from core.message import DongleMessage
from core.utils import threaded


class DongleRecvData:

    def __init__(self, content, address):
        self.__content = content
        self.__address = address

    @property
    def content(self):
        return self.__content

    @property
    def address(self):
        return self.__address

    def __eq__(self, other):
        return self.__content == other.content and self.__address == other.address


class DongleDriver:

    def __init__(self):
        self.dongle_cache = set()
        self.beacon_cache = set()
        self.prov_cache = set()
        self.message_cache = set()

        self.__dongle_communication_task_en = False

    def send(self, dongle_msg: DongleMessage):
        pass

    def recv(self):
        pass

    @threaded
    def dongle_communication_task(self):
        try:
            self.__dongle_communication_task_en = True
            while True:
                pass
        finally:
            self.__dongle_communication_task_en = False
