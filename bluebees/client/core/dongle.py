import asyncio
import base64 as b64
from asyncserial import Serial
from dataclasses import dataclass
from bluebees.common.client import Client
from bluebees.common.logging import log_sys, INFO, DEBUG
from serial.tools.list_ports import comports
from asyncio import wait_for
from serial import SerialException


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


class SearchDongle:

    def __init__(self, loop, baudrate=115200):
        self.log = log_sys.get_logger('dongle.serial')
        self.log.set_level(INFO)

        self.loop = loop
        self.baudrate = baudrate
        self.expected_result = b'@reset 0 00 bm9uZQ==\r\n***** BLE Mesh Dongle v1.0 *****\r\n'

    async def _wait_response(self, ser, port: str) -> bool:
        line = b''
        while True:
            data = await ser.read()
            line += data
            if b'\r\n' in line:
                self.log.debug(f'Result: {line}')
                if self.expected_result in line:
                    self.log.success(f'Dongle found at {port}')
                    return True

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

    async def _write_on_serial(self, ser, msg: SerialMessage):
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
            await ser.write(d)
            await asyncio.sleep(0.005)

        await asyncio.sleep(1)

    async def _try_connect(self, ser, port: str, timeout: int) -> bool:
        # send reset cmd
        serial_msg = SerialMessage(msg_type=b'reset', xmit=b'0',
                                   intms=b'00',
                                   content_b64=b64.b64encode(b'none'),
                                   address=None)
        try:
            await wait_for(self._write_on_serial(ser, serial_msg),
                           timeout=timeout)
        except asyncio.TimeoutError:
            self.log.debug(f'Dongle not found at {port}')
            return False

        # wait response
        try:
            return await wait_for(self._wait_response(ser, port),
                                  timeout=timeout)
        except asyncio.TimeoutError:
            self.log.debug(f'Dongle not found at {port}')
            return False

    def search(self) -> [str]:
        valid_ports = []
        ports = comports()
        for port, _, _ in sorted(ports):
            try:
                self.log.info(f'Testing at {port} serial port...')

                ser = Serial(self.loop, port, self.baudrate)

                result = self.loop.run_until_complete(self._try_connect(ser, port, 2))

                if result:
                    valid_ports.append(port)

            except SerialException:
                self.log.warning(f'Serial port {port} not available')

        return valid_ports


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

        self.loop.run_until_complete(self._reset_dongle())

        self.all_tasks += [self._read_serial_task(),
                           self._transport_message_task(),
                           self._write_serial_task(),
                           self._clear_caches_task()]

    async def _reset_dongle(self):
        line = b''
        expected_result = b'***** BLE Mesh Dongle v1.0 *****\r\n'
        for x in range(3):
            self.ser_log.info('Trying reset dongle...')
            serial_msg = SerialMessage(msg_type=b'reset', xmit=b'0',
                                       intms=b'00',
                                       content_b64=b64.b64encode(b'none'),
                                       address=None)
            await self._write_on_serial(serial_msg)

            # clear send message
            data = await self.serial.read(22)

            while True:
                data = await self.serial.read()
                line += data
                if b'\r\n' in line:
                    if line == expected_result:
                        self.ser_log.success('Dongle resetted')
                        return
                    line = b''
                    break
        self.ser_log.warning('Give-up to reset dongle')

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
                if line[0:1] == b'*':
                    self.ser_log.info(line.decode('utf-8'))
                if line[0:1] == b'!':
                    self.ser_log.warning(line[1:].decode('utf-8'))
                elif line[0:1] != b'@':
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
