#!/usr/bin/python3
from core.pb_adv import PbAdv
from core.utils import threaded
from core.link import Link
from core.transaction import Transaction


class GProv:

    def __init__(self):
        self.__pb_adv = PbAdv()
        self.__link = []

    @staticmethod
    def is_link_ack_pdu(payload: bytes):
        return payload[0] == 0x07

    @staticmethod
    def is_link_close_pdu(payload: bytes):
        return payload[0] == 0x0B

    @threaded
    def __check_unexpected_close_link_pdu(self, link: Link):
        while link.is_open:
            tr_number, payload = self.__pb_adv.read(link)
            if tr_number == link.transaction_number and self.is_link_close_pdu(payload):
                link.is_open = False
                link.close_reason = payload[1]

    def open_link(self, link: Link):
        if link.is_open:
            raise Exception

        # send open link pdu
        pdu = b'\x03' + link.device_uuid.address
        self.__pb_adv.write(link, pdu)
        tr = Transaction(link.transaction_number)

        # wait the link ack pdu
        while not tr.was_ack and tr.elapsed_time < GProvSettings().link_ack_timeout:
            tr_number, payload = self.__pb_adv.read(link)
            if tr_number == tr.transaction_number and self.is_link_ack_pdu(payload):
                tr.was_ack = True
            tr.increase_elapsed_time()

        link.is_open = True

        self.__check_unexpected_close_link_pdu(link)

    def close_link(self, link: Link):
        if not link.is_open:
            raise Exception

        # send close link pdu
        pdu = b'\x0B' + link.close_reason.to_bytes(1, 'big')
        self.__pb_adv.write(link, pdu)

        link.is_open = False

    def write(self, link: Link, payload: bytes):
        if not link.is_open:
            raise Exception

        # segment payload

        # send start transaction (part 2)

        # start a timer

        # send continuation transaction

        # receive transaction ack?
        #   not - the timer is less then 30s?
        #       not - cancel transaction and close link and stop provisioning
        #       yes - goto part 2
        #   yes - transaction is complete and stop timer

    def read(self, link: Link):
        if not link.is_open:
            raise Exception

        transaction_number, payload = self.__pb_adv.read(link)

    @threaded
    def read_in_background(self, link: Link, ready_callback):
        ready_callback(self.read(link))
