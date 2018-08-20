#!/usr/bin/python3
from core.link import Link
from core.settings import PbAdvSettings
from core.utils import threaded
from core.adv import AdvDriver
from math import ceil


class PbAdv:

    def __init__(self):
        self.__adv_driver = AdvDriver()

    @staticmethod
    def __segment_payload(payload: bytes):
        payload_length = len(payload)
        mtu_max_size = PbAdvSettings().mtu_max_size

        if payload_length > mtu_max_size:
            last_seg_number = int(ceil(payload_length / mtu_max_size))

            for x in range(0, last_seg_number):
                yield payload[:mtu_max_size]
                payload = payload[mtu_max_size:]
        else:
            yield payload

    def write(self, link: Link, payload: bytes):
        for segment in self.__segment_payload(payload):
            pdu = link.link_id.to_bytes(4, 'big') + link.transaction_number.to_bytes(1, 'big') + segment
            self.__adv_driver.write(pdu, type_='prov')

    def read(self, link: Link):
        correct_msg_arrive = False
        while not correct_msg_arrive:
            pdu = self.__adv_driver.read(type_expected='prov')
            if pdu[0:4] == link.link_id:
                correct_msg_arrive = True

        transaction_number, payload = pdu[4], pdu[5:]
        return transaction_number, payload

    @threaded
    def read_in_background(self, link: Link, ready_callback):
        ready_callback(self.read(link))
