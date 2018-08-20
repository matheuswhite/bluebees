#!/usr/bin/python3
from core.utils import threaded
from serial import Serial
from core.settings import AdvSettings


class AdvDriver:

    def __init__(self):
        self.__serial = Serial()

    @staticmethod
    def bytes_to_hexstr(data: bytes, endianness='big'):
        hexstr = ''
        for x in range(0, len(data)):
            if endianness == 'big':
                hexstr += hex(data[x])[2:]
            else:
                hexstr += hex(data[abs(x-len(data)-1)])[2:]
        return hexstr

    def write(self, payload: bytes, type_, endianness='big'):
        s = AdvSettings()
        self.__serial.baudrate = s.baud_rate
        self.__serial.port = s.port

        payload = self.bytes_to_hexstr(payload, endianness)
        pdu = '@{}:{}\n'.format(type_, payload)

        self.__serial.open()
        self.__serial.write(pdu)
        self.__serial.close()

    def read(self, type_expected):
        s = AdvSettings()
        self.__serial.baudrate = s.baud_rate
        self.__serial.port = s.port

        self.__serial.open()
        line = self.__serial.readline()
        self.__serial.close()

        if line[0] != '@':
            raise Exception
        line = line[1:-1]
        type_, payload = line.split(':')
        if type_expected != type_:
            raise Exception

        return payload

    @threaded
    def read_in_background(self, type_expected, ready_callback):
        ready_callback(self.read(type_expected))
