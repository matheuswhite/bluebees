#!/usr/bin/python3
from core.socket import Socket, Address, PDU
from serial import Serial
from core.utils import threaded

# TODO: Review the ADV max packet size
ADV_MAX_PACKET_SIZE = 66
PB_ADV = 1
GATT_ADV = 2


class DonglePDU(PDU):

    def __init__(self, prov_bearer: int, payload: bytes):
        super().__init__(int(prov_bearer).to_bytes(1, 'big') + len(payload).to_bytes(1, 'big') + payload)


class DongleSocket(Socket):

    def __init__(self, address: str, baudrate: int, max_read_size=ADV_MAX_PACKET_SIZE):

        super().__init__(Address.SerialPort(address))

        self.__baudrate = baudrate
        self.__max_read_size = max_read_size
        self.__serial = Serial()

    def open(self):
        super().open()
        self.__serial.baudrate = self.baudrate
        self.__serial.port = self.address.value
        self.__serial.open()

    def write(self, payload: DonglePDU):
        super().write(payload)
        self.__serial.write(payload.value)

    def read(self):
        super().read()
        payload = self.__serial.read(self.__max_read_size)
        return payload[2:]

    def close(self):
        super().close()

    @property
    def baudrate(self):
        return self.__baudrate

    @property
    def max_read_size(self):
        return self.__max_read_size

    @max_read_size.setter
    def max_read_size(self, value: int):
        self.__max_read_size = value
