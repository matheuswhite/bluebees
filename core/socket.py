#!/usr/bin/python3
import platform


class EmptyAddressError(Exception):
    pass


class SocketNotOpenError(Exception):
    pass


class SocketAlreadOpen(Exception):
    pass


class Address:

    def __init__(self, value):
        self.__value = value

    @property
    def value(self):
        return self.__value

    # TODO: Move it to a class
    @classmethod
    def SerialPort(cls, value: str):
        return cls(value)

    @classmethod
    def UUID(cls, value: bytes):
        return cls(value)


class PDU:

    def __init__(self, value: bytes):
        self.__value = value

    @property
    def value(self):
        return self.__value


class Socket:

    def __init__(self, address: Address):
        if address is None:
            raise EmptyAddressError
        self.__address = address
        self.__is_open = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        if self.__is_open:
            raise SocketAlreadOpen
        self.__is_open = True

    def write(self, payload: PDU):
        if not self.__is_open:
            raise SocketNotOpenError

    async def read(self):
        if not self.__is_open:
            raise SocketNotOpenError

    def close(self):
        if not self.__is_open:
            raise SocketNotOpenError
        self.__is_open = False

    @property
    def address(self):
        return self.__address

    @property
    def is_open(self):
        return self.__is_open
