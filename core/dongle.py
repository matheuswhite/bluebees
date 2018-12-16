from data_structs.dongle_cache import DongleCache
from core.utils import threaded
from time import sleep
from data_structs.buffer import Buffer
from dataclasses import dataclass
from core.log import Log, LogLevel
import base64
import binascii

log = Log('Dongle', LogLevel.Wrn)

MAX_MTU = 24

@dataclass
class DongleData:
    msg_type: str
    content: bytes
    address: bytes

class DongleDriver:

    def __init__(self, serial):
        self.cache = DongleCache()

        self.ser = serial
        self.ser.open()

        self.is_alive = True
        self.recv_is_alive = False
        self.dongle_communication_task()

#region Threads
    @threaded
    def dongle_communication_task(self):
        try:
            self.recv_is_alive = True
            while self.is_alive:
                try:
                    raw_msg = self.ser.readline()

                    dongle_data = self._decode_dongle_message(raw_msg)

                    if len(self.cache['adv']) > 20:
                        self.cache['adv'].clear_all()

                    if self.cache['adv'].push(dongle_data):
                        if self.cache[dongle_data.msg_type] is not None:
                            self.cache[dongle_data.msg_type].push(dongle_data.content)
                except binascii.Error:
                    log.wrn("binascii Error occurs")
                    pass
        finally:
            log.err("Exception occurs in dongle recv thread. This thread isn't alive anymore")
            self.is_alive = False
#endregion

#region Private
    def _split_data(self, data: bytes) -> list:
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

    def _decode_dongle_message(self, raw_msg: bytes):
        parts = raw_msg.split(b' ')
        if len(parts) != 3:
            return None

        at_symbol = parts[0][0]
        if at_symbol != b'@':
            log.err(f'Message start with {at_symbol} instead of @')
            return None

        msg_type = parts[0][1:]
        content_b64 = parts[1]
        address = parts[2][:-2]

        if msg_type != b'beacon':
            log.dbg(f'Content: {base64.b64decode(content_b64)}')

        return DongleData(msg_type.decode('utf-8'), base64.b64decode(content_b64), address)
#endregion

#region Public
    def kill(self):
        self.is_alive = False

    def send(self, xmit, int_ms, content: bytes):
        if len(content) > MAX_MTU:
            raise Exception('Message length greater than 29 bytes')

        content_b64 = base64.encodebytes(content).decode('utf-8')[:-1]
        msg = f'@prov {xmit} {int_ms} {content_b64}\r\n'.encode('utf-8')

        parts = self._split_data(msg)
        for p in parts:
            self.ser.write(p)
            sleep(0.005)

    def recv(self, type_: str):
        if not self.recv_is_alive:
            return None

        if len(self.cache[type_]) == 0:
            return None
        else:
            return self.cache[type_].pop()
#endregion
