#!/usr/bin/python3
from core.utils import threaded
from serial import Serial
from core.settings import AdvSettings
from threading import Lock
from time import sleep

ADV_INT_DEFAULT_MS = 100
MESH_SCAN_WINDOW_MS = 10

class AdvDriver:

    def __init__(self, port, baudrate):
        self.__serial = Serial()
        self.__serial.baudrate = baudrate
        self.__serial.port = port

        self.__serial.open()
        self.__atomic_write(b'noprompt\r\n')
        self.__atomic_write(b'select bt_mesh\r\n')
        self.__serial.close()

        self.__lock = Lock()

    @staticmethod
    def bytes_to_hexstr(data: bytes, endianness='big'):
        hexstr = ''
        for x in range(0, len(data)):
            if endianness == 'big':
                hexstr += hex(data[x])[2:]
            else:
                hexstr += hex(data[-x-1])[2:]
        return hexstr

    def __atomic_write(self, payload: bytes):
        self.__serial.write(payload)
        self.__serial.flush()

    def __write_delay(self, xmit, int_ms):
        adv_int = max(ADV_INT_DEFAULT_MS, (((int_ms >> 3) + 1) * 10))
        duration = MESH_SCAN_WINDOW_MS + (((xmit & 0x07) + 1) * (adv_int + 10))
        '''
        Incrementei a duração pois havia uma perda de 5% dos pacotes recebidos
        Caso o usuario queira aumentar a velocidade de escrita das mensagens, 
        diminuir a variável 'duration'
        
        Nova perda de pacotes ≃ 1%
        '''
        duration += duration/2
        sleep(duration/1000.0)

    def write(self, payload: bytes, type_, xmit, int_ms, endianness='big'):
        payload = self.bytes_to_hexstr(payload, endianness)
        pdu = bytes('@{} {} {} {}\r\n'.format(type_, xmit, int_ms, payload).encode('utf8'))

        self.__lock.acquire()
        self.__serial.open()
        self.__atomic_write(pdu)
        self.__serial.close()
        self.__write_delay(xmit, int_ms)
        self.__lock.release()

    def read(self, type_expected):
        line = '!'

        while line[0] != '@':
            self.__lock.acquire()
            self.__serial.open()
            line = self.__serial.readline()
            line = line.decode('utf-8')
            # print(line)
            self.__serial.close()
            self.__lock.release()

        line = line[1:-2]
        type_, payload, addr = line.split(' ')
        if type_expected != type_:
            raise Exception

        return payload, addr

    @threaded
    def read_in_background(self, type_expected, ready_callback):
        ready_callback(self.read(type_expected))
