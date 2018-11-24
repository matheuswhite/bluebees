#!/usr/bin/python3
from random import randint


class Roulette:

    def __init__(self):
        super().__init__()

        self.roulette = []

    def new_link_id(self):
        if len(self.roulette) >= 2**32:
            raise Exception()

        id_ = randint(0, (2 ** 32) - 1)
        while id_ in self.roulette:
            id_ = randint(0, (2 ** 32) - 1)

        return id_


_roulette = Roulette()


class Link:

    def __init__(self, link_id=0x100000000):
        self.device_uuid = b''
        self.link_id = _roulette.new_link_id() if link_id == 0x100000000 else link_id
        self.is_open = False
        self.close_reason = b'\x00'
        self.transaction_number = 0x00
        self.device_transaction_number = 0x80

    def increment_transaction_number(self):
        self.transaction_number += 1
        self.transaction_number %= 0x80

    def increment_device_transaction_number(self):
        self.device_transaction_number += 1
        self.device_transaction_number %= 0x80
        self.device_transaction_number += 0x80

    def get_adv_header(self):
        return self.link_id.to_bytes(4, 'big') + self.transaction_number.to_bytes(1, 'big')

    def get_dev_adv_header(self):
        return self.link_id.to_bytes(4, 'big') + self.device_transaction_number.to_bytes(1, 'big')
