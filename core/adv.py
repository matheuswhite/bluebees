#!/usr/bin/python3
from core.utils import threaded
from serial import Serial
from core.settings import AdvSettings
from threading import Lock


class AdvDriver:

    def __init__(self):
        s = AdvSettings()
        self.__serial = Serial()
        self.__serial.baudrate = s.baud_rate
        self.__serial.port = s.port

        self.__serial.open()
        self.__serial.write('noprompt\r\n')
        self.__serial.write('select bt_mesh\r\n')
        self.__serial.close()

        self.__lock = Lock()

    @staticmethod
    def __bytes_to_hexstr(data: bytes, endianness='big'):
        hexstr = ''
        for x in range(0, len(data)):
            if endianness == 'big':
                hexstr += hex(data[x])[2:]
            else:
                hexstr += hex(data[abs(x-len(data)-1)])[2:]
        return hexstr

    def write(self, payload: bytes, type_, xmit, duration, endianness='big'):
        payload = self.__bytes_to_hexstr(payload, endianness)
        pdu = '@{} {} {} {}\r\n'.format(type_, xmit, duration, payload)

        self.__lock.acquire()
        s = AdvSettings()
        self.__serial.baudrate = s.baud_rate
        self.__serial.port = s.port
        self.__serial.open()
        self.__serial.write(pdu)
        self.__serial.readline()
        self.__serial.close()
        self.__lock.release()

    def read(self, type_expected):
        line = '!'

        while line[0] != '@':
            self.__lock.acquire()
            s = AdvSettings()
            self.__serial.baudrate = s.baud_rate
            self.__serial.port = s.port
            self.__serial.open()
            line = self.__serial.readline()
            self.__serial.close()
            self.__lock.release()

        line = line[1:-2]
        type_, payload = line.split(' ')
        if type_expected != type_:
            raise Exception

        return payload

    @threaded
    def read_in_background(self, type_expected, ready_callback):
        ready_callback(self.read(type_expected))
