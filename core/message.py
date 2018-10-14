import base64
from enum import Enum

from core.buffer import Buffer
from core.link import Link


class Message:

    def __init__(self):
        self.header = Buffer()
        self.payload = Buffer()

    def to_bytes(self):
        return self.header.buffer + self.payload.buffer

    def encode_msg(self, **kwargs):
        pass

    def decode_msg(self, buffer: Buffer):
        pass


class BearerOp(Enum):
    LINK_OPEN = 0x00
    LINK_ACK = 0x01
    LINK_CLOSE = 0x02


class GProvMessageType(Enum):
    START = 0
    ACK = 1
    CONTINUATION = 2
    BEARER_CONTROL = 3


class DongleMessage(Message):

    def __init__(self):
        super().__init__()

    def encode_msg(self, xmit, int_ms, content: bytes):
        header = bytes('@prov {} {}'.format(xmit, int_ms))
        self.header.push_be(header)

        content_b64 = base64.encodebytes(content)
        self.payload.push_be(content_b64)
        self.payload.push_u8(ord('\n'))

    def decode_msg(self, buffer: Buffer):
        at_symbol = buffer.pull_u8()
        if at_symbol != b'@':
            raise Exception('Dongle messages must start with @ symbol')

        type_ = buffer.pull_be16()
        type_ += buffer.pull_be16()
        if type_ != b'prov':
            raise Exception('This class only handle prov messages')

        # space
        _ = buffer.pull_be16()

        content_b64 = b''
        byte = buffer.pull_u8()
        while byte != b'\n':
            content_b64 += byte
            byte = buffer.pull_u8()

        return base64.decodebytes(content_b64)


class PbAdvMessage(Message):

    def __init__(self):
        super().__init__()

    def encode_msg(self, link: Link, content: bytes):
        self.header.push_be32(link.link_id)
        self.header.push_u8(link.transaction_number)

        self.payload.push_be(content)

    def decode_msg(self, buffer: Buffer):
        link_id = buffer.pull_be32()
        tr_number = buffer.pull_u8()
        content = buffer.buffer

        return link_id, tr_number, content


class GProvMessage(Message):

    def __init__(self):
        super().__init__()

    def encode_msg(self, type_: GProvMessageType, **kwargs):
        if type_ == GProvMessageType.START:
            self.encode_msg_start(kwargs.get('seg_n'), kwargs.get('total_length'), kwargs.get('fcs'),
                                  kwargs.get('content'))
        elif type_ == GProvMessageType.ACK:
            self.encode_msg_ack()
        elif type_ == GProvMessageType.CONTINUATION:
            self.encode_msg_continuation(kwargs.get('index'), kwargs.get('content'))
        elif type_ == GProvMessageType.BEARER_CONTROL:
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

    def encode_msg_bearer_control(self, link: Link, bearer_op: BearerOp):
        op_code = ((bearer_op.value << 2) | 0b0000_0011)
        self.header.push_u8(op_code)

        if op_code == BearerOp.LINK_OPEN:
            self.payload.push_be(link.device_uuid.address)
        elif op_code == BearerOp.LINK_CLOSE:
            self.payload.push_be(link.close_reason)

    def decode_msg(self, buffer: Buffer):
        type_ = buffer.seek(0) & 0b0000_0011
        type_ = GProvMessageType(type_)

        if type_ == GProvMessageType.START:
            func_output = self.decode_msg_start(buffer)
        elif type_ == GProvMessageType.ACK:
            func_output = self.decode_msg_ack(buffer)
        elif type_ == GProvMessageType.CONTINUATION:
            func_output = self.decode_msg_continuation(buffer)
        elif type_ == GProvMessageType.BEARER_CONTROL:
            func_output = self.decode_msg_bearer_control(buffer)
        else:
            raise Exception('Generic Provisioning message unknown')

        return type_, func_output

    def decode_msg_start(self, buffer: Buffer):
        first_byte = buffer.pull_u8()
        seg_n = (first_byte & 0b1111_1100) >> 2

        total_length = buffer.pull_be16()
        fcs = buffer.pull_u8()
        content = buffer.buffer

        return seg_n, total_length, fcs, content

    def decode_msg_ack(self, buffer: Buffer):
        first_byte = buffer.pull_u8()
        padding = (first_byte & 0b1111_1100) >> 2
        if padding != 0:
            raise Exception('Padding of Ack message is not zero')

    def decode_msg_continuation(self, buffer: Buffer):
        first_byte = buffer.pull_u8()
        seg_index = (first_byte & 0b1111_1100) >> 2
        content = buffer.buffer

        return seg_index, content

    def decode_msg_bearer_control(self, buffer: Buffer):
        first_byte = buffer.pull_u8()
        op_code = (first_byte & 0b1111_1100) >> 2
        op_code = BearerOp(op_code)

        if op_code == BearerOp.LINK_OPEN:
            uuid = buffer.buffer
            return op_code, uuid
        elif op_code == BearerOp.LINK_CLOSE:
            close_reason = buffer.pull_u8()
            return op_code, close_reason
        elif op_code == BearerOp.LINK_ACK:
            return op_code
        else:
            raise Exception('Bearer Op code Unknown')

