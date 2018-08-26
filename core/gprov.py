#!/usr/bin/python3
from core.pb_adv import PbAdv
from core.utils import threaded
from core.link import Link
from core.transaction import Transaction
from core.settings import GProvSettings, PbAdvSettings
from time import sleep
from random import randint
import crc8


class GProv:

    def __init__(self):
        self.__pb_adv = PbAdv()
        self.__link = []

    @staticmethod
    def __is_link_ack_pdu(payload: bytes):
        return payload[0] == 0x07

    @staticmethod
    def __is_link_close_pdu(payload: bytes):
        return payload[0] == 0x0B

    @staticmethod
    def __is_tr_ack_pdu(payload: bytes):
        return payload[0] == 0x01

    @staticmethod
    def __segment_payload(payload: bytes):
        pbadv_s = PbAdvSettings()
        start_len = pbadv_s.mtu_max_size - 4
        cont_len = pbadv_s.mtu_max_size - 1

        # start
        segments = [payload[0:start_len]]
        payload = payload[start_len:]

        # continuation
        while len(payload) > cont_len:
            segments.append(payload[0:cont_len])
            payload = payload[cont_len]

        segments.append(payload)

        return segments

    @staticmethod
    def __fcs(payload: bytes):
        hash_ = crc8.crc8()
        hash_.update(payload)
        return int(hash_.hexdigest(), 16)

    @threaded
    def __check_unexpected_close_link_pdu(self, link: Link):
        while link.is_open:
            tr_number, payload = self.__pb_adv.read(link)
            if tr_number == link.transaction_number and self.__is_link_close_pdu(payload):
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
        while not tr.was_ack:
            # check timeout
            if tr.elapsed_time >= GProvSettings().link_ack_timeout:
                raise Exception

            tr_number, payload = self.__pb_adv.read(link)
            if tr_number == tr.transaction_number and self.__is_link_ack_pdu(payload):
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

        gprov_s = GProvSettings()

        # segment payload
        segments = self.__segment_payload(payload)

        ack = False
        while not ack:
            # send start transaction (part 2)
            start_segment = segments[0]
            pdu = int((len(segments) - 1) << 2).to_bytes(1, 'big') + len(payload).to_bytes(2, 'big') \
                                                                   + self.__fcs(payload).to_bytes(1, 'big') \
                                                                   + start_segment
            self.__pb_adv.write(link, pdu)

            # start a timer of 30s
            tr = Transaction(link.transaction_number)

            if len(segments) > 1:
                # start a delay
                sleep(randint(gprov_s.min_delay, gprov_s.max_delay))

                for index in range(1, len(segments)):
                    # send continuation transaction
                    pdu = int((index << 2) | 0x02).to_bytes(1, 'big') + segments[index]
                    self.__pb_adv.write(link, pdu)

                    # start a delay
                    sleep(randint(gprov_s.min_delay, gprov_s.max_delay))

            # start a delay
            sleep(gprov_s.delay_util_ack_check)

            tr_number, payload = self.__pb_adv.read(link)

            if tr_number == link.transaction_number and self.__is_tr_ack_pdu(payload):
                tr.stop_timer()
                ack = True
            elif tr.get_timer_value() >= gprov_s.tr_ack_timeout:
                tr.stop_timer()
                self.close_link(link)
                # stop provisioning
                raise Exception

    # TODO: Review the method read of gprov layer, in exception cases
    def read(self, link: Link):
        gprov_s = GProvSettings()

        while True:
            if not link.is_open:
                raise Exception

            # receive the start transaction (part 1)
            while True:
                tr_number, payload = self.__pb_adv.read(link)
                if tr_number == link.transaction_number:
                    break
            seg_number = payload[0:1] >> 2
            fcs = payload[3:4]
            prov_pdu = payload[4:]
            total_len = int(payload[2] | payload[1] << 8) - len(prov_pdu)

            # receive the continuation transaction
            for x in range(1, seg_number):
                while True:
                    tr_number, payload = self.__pb_adv.read(link)
                    if tr_number == link.transaction_number:
                        break
                if (payload[0] >> 2) > seg_number:
                    raise Exception
                total_len -= len(payload[1:])
                if total_len < 0:
                    raise Exception
                prov_pdu += payload[1:]

            if fcs == self.__fcs(prov_pdu):
                # start a delay
                sleep(randint(gprov_s.min_delay, gprov_s.max_delay))

                # send tr ack
                pdu = b'\x01'
                self.__pb_adv.write(link, pdu)

                break

    @threaded
    def read_in_background(self, link: Link, ready_callback):
        ready_callback(self.read(link))
