from data_structs.dongle_cache import DongleCache
from core.utils import threaded
from time import sleep
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

    return DongleData(type_.decode('utf-8'), base64.decodebytes(content_b64), address)


class DongleDriver:

    def __init__(self, serial):
        self.cache = DongleCache()

        self.__ser = serial
        self.__ser.open()

        self.__dongle_communication_task_en = False

    def __split_data(self, data: bytes):
        datas = []
        part = b''

        for byte in data:
            if len(part) >= 5:
                datas.append(part)
                part = b''
            part += byte.to_bytes(1, 'big')

        if len(part) > 0:
            datas.append(part)

        return datas

    def send(self, xmit, int_ms, content: bytes):
        if len(content) > 29:
            raise Exception('Message length greater than 24 bytes')

        content_b64 = base64.encodebytes(content).decode('utf-8')[:-1]
        msg = f'@prov {xmit} {int_ms} {content_b64}\r\n'.encode('utf-8')

        parts = self.__split_data(msg)
        for p in parts:
            self.__ser.write(p)
            sleep(0.005)

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

                if self.cache['adv'].push(dongle_data):
                    self.cache[dongle_data.type_].push(dongle_data.content)
        finally:
            self.__dongle_communication_task_en = False
