#!/usr/bin/python3
from random import randint
from core.utils import HandSide


class Roulette:

    def __init__(self):
        super().__init__()

        self.roulette = []

    def new_link_id(self):
        if len(self.roulette) >= 2**4:
            raise Exception

        id = randint(0, (2**4)-1)
        while id in self.roulette:
            id = randint(0, (2 ** 4) - 1)

        return id


_roulette = Roulette()


class Link:

    def __init__(self, device_uuid: bytes, handside=HandSide.Provisioner):
        self.__device_uuid = device_uuid
        self.__link_id = _roulette.new_link_id()
        self.__handside = handside
        self.is_open = False
        self.close_reason = 0x00
        if self.__handside == HandSide.Provisioner:
            self.__transaction_number = 0x00
        elif self.__handside == HandSide.Device:
            self.__transaction_number = 0x80

    @property
    def device_uuid(self):
        return self.__device_uuid

    @property
    def link_id(self):
        return self.__link_id

    @property
    def transaction_number(self):
        return self.__transaction_number

    def increment_transaction_number(self):
        self.__transaction_number += 1
        if self.__handside == HandSide.Provisioner:
            self.__transaction_number %= 0x80
        elif self.__handside == HandSide.Device:
            self.__transaction_number = (self.__transaction_number % 0x80) + 0x80
        return self.__transaction_number
