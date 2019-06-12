import asyncio
import base64 as b64
from asyncserial import Serial
from dataclasses import dataclass
from bluebees.common.client import Client
from bluebees.common.logging import log_sys, INFO, DEBUG


@dataclass
class DongleMessage:
    msg_type: bytes
    content: bytes


@dataclass
class SerialMessage:
    msg_type: bytes
    xmit: bytes
    intms: bytes
    content_b64: bytes
    address: bytes


class Dongle(Client):

    def __init__(self, loop, serial_port, baudrate=115200):
        super().__init__(sub_topic_list=[b'message_s', b'prov_s'],
                         pub_topic_list=[b'message', b'prov', b'beacon'])

        self.ser_log = log_sys.get_logger('dongle.serial')
        self.ch_log = log_sys.get_logger('dongle.channel')
        self.ser_log.set_level(DEBUG)
        self.ch_log.set_level(DEBUG)

        self.loop = loop
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.serial = Serial(self.loop, self.serial_port, self.baudrate)
        self.write_serial_queue = asyncio.Queue()

        self.caches = {
            b'message': [],
            b'beacon': [],
            b'prov': []
        }

        self.all_tasks += [self._read_serial_task(),
                           self._transport_message_task(),
                           self._write_serial_task(),
                           self._clear_caches_task()]

    async def _clear_caches_task(self):
        while True:
            await asyncio.sleep(5 * 60)
            self.ser_log.info('Cleaning caches...')
            self.caches = {
                b'message': [],
                b'beacon': [],
                b'prov': []
            }
            self.ser_log.info('Caches clean')

    async def _read_serial_task(self):
        while True:
            serial_msg = await self._read_from_serial()

            self.ser_log.debug(f'Got a message with type {serial_msg.msg_type} and '
                               f'content {b64.b64decode(serial_msg.content_b64).hex()}')

            dongle_msg = self._translate_serial_message(serial_msg)

            await self.messages_to_send.put((dongle_msg.msg_type,
                                             dongle_msg.content))

    async def _transport_message_task(self):
        while True:
            (msg_type, content) = await self.messages_received.get()
            self.ch_log.debug(f'Got a message with type {msg_type} and content {content.hex()}')
            dongle_msg = DongleMessage(msg_type, content)

            serial_msg = self._translate_dongle_message(dongle_msg)

            await self.write_serial_queue.put(serial_msg)

    async def _write_serial_task(self):
        while True:
            serial_msg = await self.write_serial_queue.get()
            self.ser_log.debug(f'Send a message with type {serial_msg.msg_type} and '
                               f'content {b64.b64decode(serial_msg.content_b64).hex()}')

            await self._write_on_serial(serial_msg)

    async def _read_from_serial(self):
        line = b''
        while True:
            data = await self.serial.read()
            line += data
            if b'\r\n' in line:
                if line[0:1] != b'@':
                    line = b''
                    continue

                parts = line.split(b' ')

                if len(parts) != 3:
                    line = b''
                    continue

                msg = SerialMessage(msg_type=parts[0][1:], xmit=None,
                                    intms=None,
                                    content_b64=parts[1],
                                    address=parts[2][:-2])

                if msg in self.caches[msg.msg_type]:
                    line = b''
                    continue
                self.caches[msg.msg_type].append(msg)

                return msg

    def _split_data(self, data: bytes):
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

    async def _write_on_serial(self, msg: SerialMessage):
        data = b'@'
        data += msg.msg_type
        data += b' '
        data += msg.xmit
        data += b' '
        data += msg.intms
        data += b' '
        data += msg.content_b64
        data += b'\r\n'

        datas = self._split_data(data)
        for d in datas:
            await self.serial.write(d)
            await asyncio.sleep(0.005)

        await asyncio.sleep(1)

    def _translate_serial_message(self, msg: SerialMessage) -> DongleMessage:
        dongle_msg = DongleMessage(msg_type=msg.msg_type,
                                   content=b64.b64decode(msg.content_b64))
        return dongle_msg

    def _translate_dongle_message(self, msg: DongleMessage) -> SerialMessage:
        serial_msg = SerialMessage(msg_type=msg.msg_type[:-2], xmit=b'2',
                                   intms=b'20',
                                   content_b64=b64.b64encode(msg.content),
                                   address=None)
        return serial_msg
