#!/usr/bin/python3
from math import ceil
from core.dongle_socket import *
from core.provisioning_bearer import ProvisioningBearerSocket
from random import randrange
from threading import Timer
from core.transaction_number import TransactionNumber

ADV_MTU_SIZE = 24
LINK_CLOSE_SUCESS = b'\x00'
LINK_CLOSE_TIMEOUT = b'\x01'
LINK_CLOSE_FAIL = b'\x02'


class CloseLinkFromDeviceError(Exception):

    def __init__(self, reason):
        self.reason = reason


class ProvisioningBearerADVPDU(PDU):

    def __init__(self, link_id: int, transaction_number: int, payload: bytes):
        super().__init__(int(link_id).to_bytes(4, 'big') + int(transaction_number).to_bytes(1, 'big') + payload)


class ProvisioningBearerADVSocket(ProvisioningBearerSocket):

    def __init__(self, device_uuid: bytes, dongle_port: str):
        super().__init__(device_uuid, dongle_port)

        self.__link_id = None
        self.__transaction_number = None
        self.__close_reason = LINK_CLOSE_SUCESS
        self.__timer = Timer(30.0, self.__check_incoming_ack)
        self.__has_ack = False

    @staticmethod
    def __get_link_id():
        return randrange(0, 0xFFFFFFFF)

    @staticmethod
    def __segment_payload(payload):
        payload_length = len(payload)

        if payload_length > ADV_MTU_SIZE:
            last_seg_number = int(ceil(payload_length / ADV_MTU_SIZE))

            for x in range(0, last_seg_number):
                yield payload[:ADV_MTU_SIZE]
                payload = payload[ADV_MTU_SIZE:]
        else:
            yield payload

    def __check_incoming_ack(self):
        if not self.__has_ack:
            self.__close_reason = LINK_CLOSE_TIMEOUT

    def open(self):
        super().open()

        with DongleSocket(self._dongle_port, 115200) as socket:
            self.__link_id = self.__get_link_id()
            self.__transaction_number = TransactionNumber()
            self.__close_reason = LINK_CLOSE_SUCESS

            pbadv_pdu = ProvisioningBearerADVPDU(self.__link_id, next(self.__transaction_number),
                                                 payload=(b'\x03' + self.address.value))
            dongle_pdu = DonglePDU(prov_bearer=PB_ADV, payload=pbadv_pdu.value)

            socket.write(dongle_pdu)

            self.__timer.start()

    def close(self):
        super().close()

        self.__timer.cancel()

        with DongleSocket(self._dongle_port, 115200) as socket:
            pbadv_pdu = ProvisioningBearerADVPDU(self.__link_id, next(self.__transaction_number),
                                                 payload=(b'\x0B' + self.__close_reason))
            dongle_pdu = DonglePDU(prov_bearer=PB_ADV, payload=pbadv_pdu.value)

            socket.write(dongle_pdu)

    def write(self, payload: PDU):
        super().write(payload)

        with DongleSocket(self._dongle_port, 115200) as socket:
            tr_number = next(self.__transaction_number)

            for segment in self.__segment_payload(payload.value):
                pbadv_pdu = ProvisioningBearerADVPDU(self.__link_id, tr_number, segment)
                dongle_pdu = DonglePDU(prov_bearer=PB_ADV, payload=pbadv_pdu.value)

                socket.write(dongle_pdu)

    def read(self):
        super().read()

        with DongleSocket(self._dongle_port, 115200) as socket:
            pdu = socket.read()
            payload = pdu[5:]

            # Provisioning Bearer Control
            if payload[0:1] & b'\x03' == b'\x03':
                bearer_opcode = payload[0:1] & b'\b11111100'

                # if a link ack msg arrive, then stop timer
                if bearer_opcode == b'\x01':
                    self.__timer.cancel()

                # if a link close arrive, raise a exception with the reason ('close the link')
                if bearer_opcode == b'\x02':
                    raise CloseLinkFromDeviceError(reason=payload[1:2])

            # remove the header of this layer and then send the payload to next layer
            return payload
