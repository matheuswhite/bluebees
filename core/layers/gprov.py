from enum import Enum
from core.message import Message
from core.link import Link
from core.buffer import Buffer
from .pb_adv import PbAdvMessage


LINK_OPEN = 0x00
LINK_ACK = 0x01
LINK_CLOSE = 0x02

MAX_MTU_SIZE = 24


class GProvMessage(Message):

    def __init__(self):
        super().__init__()

    # ***ENCODING***

    def encode_msg(self, type_, **kwargs):
        if type_ == 'start':
            self.encode_msg_start(kwargs.get('seg_n'), kwargs.get('total_length'), kwargs.get('fcs'),
                                  kwargs.get('content'))
        elif type_ == 'ack':
            self.encode_msg_ack()
        elif type_ == 'continuation':
            self.encode_msg_continuation(kwargs.get('index'), kwargs.get('content'))
        elif type_ == 'bearer_control':
            self.encode_msg_bearer_control(kwargs.get('link'), kwargs.get('bearer_op'))
        else:
            raise Exception('Generic Provisioning message unknown')

    def encode_msg_start(self, seg_n, total_length, fcs, content: bytes):
        last_seg_number = (seg_n & 0b0011_1111) << 2
        self.header.push_u8(last_seg_number)
        self.header.push_be16(total_length)
        self.header.push_u8(fcs)

        self.payload.push_be(content)

    def encode_msg_ack(self):
        self.header.push_u8(0b0000_0001)

    def encode_msg_continuation(self, index, content: bytes):
        seg_index = ((index & 0b0011_1111) << 2 | 0b0000_0010)
        self.header.push_u8(seg_index)

        self.payload.push_be(content)

    def encode_msg_bearer_control(self, link: Link, bearer_op):
        op_code = ((bearer_op.value << 2) | 0b0000_0011)
        self.header.push_u8(op_code)

        if op_code == LINK_OPEN:
            self.payload.push_be(link.device_uuid.address)
        elif op_code == LINK_CLOSE:
            self.payload.push_be(link.close_reason)

    # ***DECODING***

    @staticmethod
    def decode_msg(buffer: Buffer):
        type_ = buffer.seek(0) & 0b0000_0011

        if type_ == 'start':
            func_output = GProvMessage.decode_msg_start(buffer)
        elif type_ == 'ack':
            func_output = GProvMessage.decode_msg_ack(buffer)
        elif type_ == 'continuation':
            func_output = GProvMessage.decode_msg_continuation(buffer)
        elif type_ == 'bearer_control':
            func_output = GProvMessage.decode_msg_bearer_control(buffer)
        else:
            raise Exception('Generic Provisioning message unknown')

        return type_, func_output

    @staticmethod
    def decode_msg_start(buffer: Buffer):
        first_byte = buffer.pull_u8()
        seg_n = (first_byte & 0b1111_1100) >> 2

        total_length = buffer.pull_be16()
        fcs = buffer.pull_u8()
        content = buffer.buffer

        return seg_n, total_length, fcs, content

    @staticmethod
    def decode_msg_ack(buffer: Buffer):
        first_byte = buffer.pull_u8()
        padding = (first_byte & 0b1111_1100) >> 2
        if padding != 0:
            raise Exception('Padding of Ack message is not zero')

    @staticmethod
    def decode_msg_continuation(buffer: Buffer):
        first_byte = buffer.pull_u8()
        seg_index = (first_byte & 0b1111_1100) >> 2
        content = buffer.buffer

        return seg_index, content

    @staticmethod
    def decode_msg_bearer_control(buffer: Buffer):
        first_byte = buffer.pull_u8()
        op_code = (first_byte & 0b1111_1100) >> 2

        if op_code == LINK_OPEN:
            uuid = buffer.buffer
            return op_code, uuid
        elif op_code == LINK_CLOSE:
            close_reason = buffer.pull_u8()
            return op_code, close_reason
        elif op_code == LINK_ACK:
            return op_code
        else:
            raise Exception('Bearer Op code Unknown')


class GProvLayer:

    def __init__(self, pb_adv_layer):
        self.__pb_adv_layer = pb_adv_layer

    def open(self, link: Link):
        pass

    def send(self, link: Link, content: bytes):
        buffer = Buffer()
        buffer.push_be(content)

        # get_total_length
        total_length = buffer.length
        # get fcs
        fcs = self.__fcs(content)
        # get start segment
        start_content = buffer.pull_be(MAX_MTU_SIZE - 4)
        # get continuation_segments
        continuation_segments = []
        while buffer.length > (MAX_MTU_SIZE - 1):
            continuation_segments.append(buffer.pull_be(MAX_MTU_SIZE - 1))
        continuation_segments.append(buffer.pull_all_be())
        # get segN value
        segN = len(continuation_segments)


        # creating start message
        msg = GProvMessage()
        msg.encode_msg('start', segN=segN, total_length=total_length, fcs=fcs, content=start_content)

        # send others segments
        msg = PbAdvMessage()
        msg.encode_msg()
        self.__dongle_driver.send(msg)

    def recv(self):
        pass

    def close(self, link: Link):
        pass
