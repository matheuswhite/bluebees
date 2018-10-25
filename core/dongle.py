from enum import Enum
from core.message import DongleMessage
from core.utils import threaded
from time import sleep
from serial import Serial


class DongleMessageType(Enum):
    beacon = 0x00
    message = 0x01
    prov = 0x02


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

    def __init__(self, port, baudrate=115200):
        self.dongle_cache = []
        self.beacon_cache = []
        self.prov_cache = []
        self.message_cache = []

        self.__ser = Serial()
        self.__ser.port = port
        self.__ser.baudrate = baudrate

        self.__dongle_communication_task_en = False

    def send(self, dongle_msg: DongleMessage):
        self.

    def recv(self, type_: DongleMessageType, tries=float('Inf'), interval=0.5):
        if not self.__dongle_communication_task_en:
            raise Exception('dongle_communication_task not running')

        if tries == float('Inf'):
            while len(self.cache[type_]) == 0:
                pass
            return self.cache[type_].pop()
        else:
            for t in range(int(tries)):
                if len(self.cache[type_]) > 0:
                    return self.cache[type_].pop()
                sleep(interval)
            raise Exception('Reach out of max number of tries')

    @threaded
    def dongle_communication_task(self):
        try:
            self.__dongle_communication_task_en = True
            while True:
                pass
        finally:
            self.__dongle_communication_task_en = False
