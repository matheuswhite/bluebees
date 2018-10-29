from core.message import Message
from core.link import Link
from core.buffer import Buffer
from dataclasses import dataclass
from .dongle import DongleMessage


@dataclass
class PbAdvData:
    link_id: int
    tr_number: int
    content: bytes


class PbAdvMessage(Message):

    def __init__(self):
        super().__init__()

    def encode_msg(self, link: Link, content: bytes):
        self.header.push_be32(link.link_id)
        self.header.push_u8(link.transaction_number)

        self.payload.push_be(content)

    @staticmethod
    def decode_msg(buffer: Buffer):
        link_id = int(buffer.pull_be32())
        tr_number = int(buffer.pull_u8())
        content = buffer.buffer

        return PbAdvData(link_id, tr_number, content)


class PbAdvLayer:

    def __init__(self, dongle_driver):
        self.__dongle_driver = dongle_driver

    def send(self, pbadv_msg: PbAdvMessage):
        msg = DongleMessage()
        msg.encode_msg(2, 200, pbadv_msg.to_bytes())
        self.__dongle_driver.send(msg)

    def recv(self):
        buffer = Buffer()
        buffer.push_be(self.__dongle_driver.recv('prov'))

        pb_adv_data = PbAdvMessage.decode_msg(buffer)
        return pb_adv_data.content
