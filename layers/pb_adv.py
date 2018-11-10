from core.link import Link
from data_structs.buffer import Buffer
from dataclasses import dataclass


@dataclass
class PbAdvData:
    link_id: int
    tr_number: int
    content: bytes


def decode_pbadv_message(buffer: Buffer):
    link_id = int.from_bytes(buffer.pull_be32(), byteorder='big')
    tr_number = int.from_bytes(buffer.pull_u8(), byteorder='big')
    content = buffer.buffer

    return PbAdvData(link_id, tr_number, content)


class PbAdvLayer:

    def __init__(self, dongle_driver):
        self.__dongle_driver = dongle_driver

    def send(self, link: Link, content: bytes):
        buffer = Buffer()
        buffer.push_be32(link.link_id)
        buffer.push_u8(link.transaction_number)
        buffer.push_be(content)

        self.__dongle_driver.send(2, 20, buffer.buffer_be())

    def recv(self, tries=float('Inf'), interval=0.5):
        content = self.__dongle_driver.recv('prov', tries, interval)
        if content is None:
            return None

        buffer = Buffer()
        buffer.push_be(content)

        pb_adv_data = decode_pbadv_message(buffer)
        return pb_adv_data
