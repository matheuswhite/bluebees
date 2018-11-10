#!/usr/bin/python3
from random import randint


class Roulette:

    def __init__(self):
        super().__init__()

        self.roulette = []

    def new_link_id(self):
        if len(self.roulette) >= 2**32:
            raise Exception()

        id = randint(0, (2 ** 32) - 1)
        while id in self.roulette:
            id = randint(0, (2 ** 32) - 1)

        return id


_roulette = Roulette()


class Link:

    def __init__(self, device_uuid: bytes, empty_link_id=False):
        self.__device_uuid = device_uuid
        self.__link_id = _roulette.new_link_id() if not empty_link_id else None
        self.is_open = False
        self.close_reason = b'\x00'
        self.__transaction_number = 0x00

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
        self.__transaction_number %= 0x80
        return self.__transaction_number

    def get_copy(self, link, new_tr_number=None):
        self.__device_uuid = link.device_uuid
        self.__link_id = link.link_id
        self.is_open = link.is_open
        self.close_reason = link.close_reason
        self.__transaction_number = link.transaction_number if new_tr_number is None else new_tr_number
