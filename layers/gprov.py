from core.link import Link
from data_structs.buffer import Buffer
from core.utils import threaded
from time import time, sleep
from random import randint
from threading import Event
from dataclasses import dataclass
from typing import Any
import crc8


LINK_OPEN = 0x00
LINK_ACK = 0x01
LINK_CLOSE = 0x02

START = 0x00
ACKNOWLEDGMENT = 0x01
CONTINUATION = 0x02
BEARER_CONTROL = 0x03

MAX_MTU_SIZE = 24

CLOSE_SUCCESS = 0x00
CLOSE_TIMEOUT = 0x01
CLOSE_FAIL = 0x02


class UnexpectedDeviceCloseException(Exception):

    def __init__(self, close_reason):
        self.close_reason = close_reason


@dataclass
class GProvStart:
    seg_n: int
    total_length: int
    fcs: int
    content: bytes


@dataclass
class GProvContinuation:
    seg_index: int
    content: bytes


@dataclass
class GProvAck:
    content: bytes


@dataclass
class GProvBearerControl:
    op_code: int
    content: bytes


@dataclass
class GProvData:
    type_: int
    msg_params: Any


def decode_msg_start(buffer: Buffer):
    first_byte = buffer.pull_u8()
    seg_n = (int.from_bytes(first_byte, byteorder='big') & 0b1111_1100) >> 2

    total_length = buffer.pull_be16()
    fcs = buffer.pull_u8()
    content = buffer.buffer

    return GProvStart(seg_n, total_length, fcs, content)


def decode_msg_ack(buffer: Buffer):
    first_byte = buffer.pull_u8()
    padding = (int.from_bytes(first_byte, byteorder='big') & 0b1111_1100) >> 2
    if padding != 0:
        raise Exception('Padding of Ack message is not zero')

    return GProvAck(b'')


def decode_msg_continuation(buffer: Buffer):
    first_byte = buffer.pull_u8()
    seg_index = (int.from_bytes(first_byte, byteorder='big') & 0b1111_1100) >> 2
    content = buffer.buffer

    return GProvContinuation(seg_index, content)


def decode_msg_bearer_control(buffer: Buffer):
    first_byte = buffer.pull_u8()
    op_code = (int.from_bytes(first_byte, byteorder='big') & 0b1111_1100) >> 2

    if op_code == LINK_OPEN:
        uuid = buffer.buffer
        return GProvBearerControl(op_code, uuid)
    elif op_code == LINK_CLOSE:
        close_reason = buffer.pull_u8()
        return GProvBearerControl(op_code, close_reason)
    elif op_code == LINK_ACK:
        return GProvBearerControl(op_code, b'')
    else:
        raise Exception('Bearer Op code Unknown')


def decode_gprov_message(buffer: Buffer):
    type_ = int.from_bytes(buffer.seek(0), byteorder='big') & 0b0000_0011

    if type_ == START:
        func_output = decode_msg_start(buffer)
    elif type_ == ACKNOWLEDGMENT:
        func_output = decode_msg_ack(buffer)
    elif type_ == CONTINUATION:
        func_output = decode_msg_continuation(buffer)
    elif type_ == BEARER_CONTROL:
        func_output = decode_msg_bearer_control(buffer)
    else:
        raise Exception('Generic Provisioning message unknown')

    return GProvData(type_, func_output)


class GProvLayer:

    def __init__(self, pb_adv_layer):
        self.__pb_adv_layer = pb_adv_layer
        self.__ack_recv_event = Event()
        self.__ack_timeout_event = Event()
        self.__recv_state = 0

    @staticmethod
    def __check_device_close(gprov_data: GProvData):
        if gprov_data.type_ == BEARER_CONTROL:
            return gprov_data.msg_params.op_code == LINK_CLOSE

    def open(self, link: Link, timeout=30):
        msg = Buffer()
        buffer = Buffer()
        elapsed_time = 0
        opcode = 0x00

        # add open opcode (0x03)
        msg.push_u8(0x03)
        # add device uuid
        msg.push_be(link.device_uuid)

        # send open
        print(f'Opening Link {link.link_id}...')
        self.__pb_adv_layer.send(link, msg.buffer_be())

        # wait bearer control ack
        start_time = time()
        while opcode != LINK_ACK and elapsed_time < timeout:
            content = self.__pb_adv_layer.recv(1, 0.5)
            if content is not None:
                buffer.clear()
                buffer.push_be(content)
                gprov_data = decode_gprov_message(buffer)
                if gprov_data.type_ == BEARER_CONTROL:
                    opcode = gprov_data.msg_params.op_code
            elapsed_time = time() - start_time

        if opcode == LINK_ACK and elapsed_time < timeout:
            link.is_open = True
            print(f'Link {link.link_id} open.')
        else:
            print(f'Fail to open Link {link.link_id}')

        link.increment_transaction_number()

    @staticmethod
    def __fcs(buffer):
        hash_ = crc8.crc8()
        hash_.update(buffer.buffer_be())
        return int(hash_.hexdigest(), 16)

    @threaded
    def __check_tr_ack(self, link: Link):
        buffer = Buffer()
        type_ = START
        start_time = time()
        elapsed_time = 0

        while type_ != ACKNOWLEDGMENT and elapsed_time < 30:
            content = self.__pb_adv_layer.recv(1, 0.5)
            buffer.clear()
            buffer.push_be(content)
            gprov_data = decode_gprov_message(buffer)
            if self.__check_device_close(gprov_data):
                link.is_open = False
                link.close_reason = gprov_data.msg_params.content
                self.__ack_timeout_event.set()
                return
            type_ = gprov_data.type_
            elapsed_time = time() - start_time

        if type_ == ACKNOWLEDGMENT and elapsed_time < 30:
            self.__ack_recv_event.set()

        self.__ack_timeout_event.set()

    def __send_start_tr(self, link, buffer):
        # get_total_length
        total_length = buffer.length
        # get fcs
        fcs = GProvLayer.__fcs(buffer)
        # get start segment
        start_content = buffer.pull_be(MAX_MTU_SIZE - 4)
        # get continuation_segments
        continuation_segments = []
        while buffer.length > (MAX_MTU_SIZE - 1):
            continuation_segments.append(buffer.pull_be(MAX_MTU_SIZE - 1))
        continuation_segments.append(buffer.pull_all_be())
        # get segN value
        seg_n = len(continuation_segments)
        last_seg_number = (seg_n & 0b0011_1111) << 2

        msg = Buffer()
        msg.push_u8(last_seg_number)
        msg.push_be16(total_length)
        msg.push_u8(fcs)
        msg.push_be(start_content)

        delay = randint(20, 50) / 1000
        sleep(delay)

        self.__pb_adv_layer.send(link, msg.buffer_be())

        return continuation_segments

    def __send_continuation_tr(self, link, continuation_segments):
        msg = Buffer()

        for x in range(len(continuation_segments)):
            msg.clear()

            seg_index = (x+1 & 0b0011_1111) << 2 | 0b0000_0010
            msg.push_u8(seg_index)
            msg.push_be(continuation_segments[x])

            delay = randint(20, 50) / 1000
            sleep(delay)

            self.__pb_adv_layer.send(link, msg.buffer_be())

    def send(self, link: Link, content: bytes):
        buffer = Buffer()
        buffer.push_be(content)

        # send start transaction
        continuation_segments = self.__send_start_tr(link, buffer)

        # start thread to check ack response
        self.__check_tr_ack(link)

        # send
        self.__send_continuation_tr(link, continuation_segments)

        # wait ack response
        self.__ack_timeout_event.wait(30.5)
        # check if link is open yet
        if not link.is_open:
            raise UnexpectedDeviceCloseException(link.close_reason)
        # check if ack was received
        if not self.__ack_recv_event.is_set():
            # cancel tr, provisioning and close link
            raise Exception('No ack message received within 30 seconds')

        link.increment_transaction_number()

    def __atomic_recv(self):
        buffer = Buffer()
        buffer.push_be(self.__pb_adv_layer.recv())

        gprov_data = decode_gprov_message(buffer)
        return gprov_data

    # TODO: verify if FCS value on message match the FCS computed from message content
    def recv(self, link: Link):
        # get start tr
        start_data = self.__atomic_recv()

        if self.__check_device_close(start_data):
            link.is_open = False
            raise UnexpectedDeviceCloseException(start_data.msg_params.content)

        if start_data.type_ != START:
            raise Exception('First message is not start')

        content = Buffer()
        content.push_be(start_data.msg_params.content)

        # get continuation tr
        for index in range(1, start_data.msg_params.seg_n+1):
            continuation_data = self.__atomic_recv()

            if self.__check_device_close(continuation_data):
                link.is_open = False
                raise UnexpectedDeviceCloseException(continuation_data.msg_params.content)

            if continuation_data.type_ != CONTINUATION:
                raise Exception(f'Expected a continuation message, but got {continuation_data.type_}')

            if continuation_data.msg_params.seg_index != index:
                raise Exception(f'Wrong index of continuation message. Expected {index}, actual '
                                f'{continuation_data.msg_params.seg_index}')

            content.push_be(continuation_data.msg_params.content)

        # send ack
        ack_msg = Buffer()
        ack_msg.push_u8(0x01)

        self.__pb_adv_layer.send(link, ack_msg.buffer_be())

        return content.buffer_be()

    def close(self, link: Link):
        print(f'Closing Link {link.link_id}...')
        msg = Buffer()

        # add close opcode (0x0B)
        msg.push_u8(0x0B)
        # add close reason
        msg.push_u8(link.close_reason)

        # send close
        self.__pb_adv_layer.send(link, msg.buffer_be())

        link.is_open = False
        print(f'Link {link.link_id} closed. Reason: {link.close_reason}')
        link.increment_transaction_number()
