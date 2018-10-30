from data_structs.dongle_cache import DongleCache
from core.utils import threaded
from time import sleep
from serial import Serial
from data_structs.buffer import Buffer
from dataclasses import dataclass
import base64


@dataclass
class DongleData:
    type_: str
    content: bytes
    address: bytes


def decode_dongle_message(buffer: Buffer):
    at_symbol = buffer.pull_u8()
    if at_symbol != b'@':
        raise Exception('Dongle messages must start with @ symbol')

    type_ = b''
    byte = buffer.pull_u8()
    while byte != b' ':
        type_ += byte
        byte = buffer.pull_u8()

    content_b64 = b''
    byte = buffer.pull_u8()
    while byte != b' ':
        content_b64 += byte
        byte = buffer.pull_u8()

    address = b''
    byte = buffer.pull_u8()
    while byte != b'\n':
        address += byte
        byte = buffer.pull_u8()

    return DongleData(str(type_), base64.decodebytes(content_b64), address)


class DongleDriver:

    def __init__(self, port, baudrate=115200):
        self.cache = DongleCache()

        self.__ser = Serial()
        self.__ser.port = port
        self.__ser.baudrate = baudrate

        self.__dongle_communication_task_en = False

    def send(self, xmit, int_ms, content: bytes):
        content_b64 = base64.encodebytes(content)
        msg = bytes(f'@prov {xmit} {int_ms} {content_b64}\n')
        self.__ser.write(msg)

    def recv(self, type_: str, tries=float('Inf'), interval=0.5):
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
                raw_msg = self.__ser.readline()

                buffer = Buffer()
                buffer.push_be(raw_msg)

                dongle_data = decode_dongle_message(buffer)

                if len(self.cache['adv']) > 20:
                    self.cache['adv'].clear_all()

                self.cache['adv'].push(dongle_data)
                self.cache[dongle_data.type_].push(dongle_data.content)
        finally:
            self.__dongle_communication_task_en = False
