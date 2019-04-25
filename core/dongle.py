import asyncio
import zmq.asyncio
import base64 as b64
from zmq.asyncio import Context
from asyncserial import Serial
from dataclasses import dataclass


@dataclass
class DongleMessage:
    msg_type: bytes
    content: bytes
    address: bytes


class Dongle:

    def __init__(self, loop, serial_port, baudrate=115200, port=9521):
        self.loop = loop
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.serial = Serial(self.loop, self.serial_port, self.baudrate)

        self.port = port
        self.url = 'tcp://127.0.0.1:{self.port}'
        self.ctx = Context.instance()

        self.pub = self.ctx.socket(zmq.PUB)
        self.sub = self.ctx.socket(zmq.SUB)

        self.publish_queue = asyncio.Queue()
        self.subscribe_queue = asyncio.Queue()

        self.beacon_cache = []
        self.message_cache = []
        self.prov_cache = []

    def _decode_message_type(self, msg_type):
        if msg_type == b'prv':
            return b'prov'
        elif msg_type == b'msg':
            return b'message'

    def _encode_message_type(self, msg_type):
        if msg_type == b'beacon':
            return b'bcn'
        elif msg_type == b'prov':
            return b'prv'
        elif msg_type == b'message':
            return b'msg'

    async def _read_from_serial(self):
        while True:
            serial_content = await self.serial.readline()

            if serial_content[0:1] != b'@':
                continue

            serial_content: bytes = serial_content[1:]

            parts = serial_content.split(b' ')
            if len(parts) != 3:
                continue

            msg_type = parts[0][1:]
            content = b64.b64decode(parts[1])
            address = parts[2][:-2]

            if msg_type not in [b'beacon', b'prov', b'message']:
                continue

            return DongleMessage(self._encode_message_type(msg_type),
                                 content, address)

    async def _write_from_serial(self, type_: bytes, content: bytes):
        msg_type = self._decode_message_type(type_)
        xmit = 2
        int_ms = 20
        content_b64 = b64.encodebytes(content).decode('utf-8')[:-1]

        msg = f'@{msg_type} {xmit} {int_ms} {content_b64}\r\n'.encode('utf-8')

        # ? I need divide in parts
        await self.serial.write(msg)

    async def read_task(self):
        await self.serial.read()

        while True:
            dongle_msg: DongleMessage = await self._read_from_serial()

            if dongle_msg.msg_type == b'bcn' \
               and dongle_msg not in self.beacon_cache:
                self.beacon_cache.append(dongle_msg)
            elif dongle_msg.msg_type == b'prv' \
                    and dongle_msg not in self.prov_cache:
                self.prov_cache.append(dongle_msg)
            elif dongle_msg.msg_type == b'msg' \
                    and dongle_msg not in self.message_cache:
                self.message_cache.append(dongle_msg)

            await self.publish_queue.put(dongle_msg)

    async def write_task(self):
        while True:
            msg: DongleMessage = await self.subscribe_queue.get()

            # ! removing '_s' from message type
            await self._write_from_serial(msg.msg_type[0:3], msg.content)

    async def publish_task(self):
        self.pub.connect(self.url)

        await asyncio.sleep(0.3)

        while True:
            msg = await self.publish_queue.get()

            await self.pub.send_multipart([msg.msg_type, msg.content])

    async def subscribe_task(self):
        self.sub.bind(self.url)

        # ? Can I subscribe in 2 channels
        self.sub.setsockopt(zmq.SUBSCRIBE, b'prv_s')
        self.sub.setsockopt(zmq.SUBSCRIBE, b'msg_s')

        while True:
            [topic, msg] = await self.sub.recv_multipart()

            dongle_msg = DongleMessage(topic, msg)

            await self.subscribe_queue.put(dongle_msg)

    def tasks(self):
        return asyncio.gather(self.read_task(), self.write_task(),
                              self.publish_task(), self.subscribe_task())
