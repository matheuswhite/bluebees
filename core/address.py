#!/usr/bin/python3


class UUID:

    def __init__(self, address: bytes):
        self.__address = address

    @property
    def address(self):
        return self.__address
