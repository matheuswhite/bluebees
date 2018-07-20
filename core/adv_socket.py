#!/usr/bin/python3
from math import ceil
from core.dongle_socket import *
from core.provisioning_bearer import ProvisioningBearerSocket
from random import randrange
from core.transaction_number import TransactionNumber

ADV_MTU_SIZE = 24
LINK_CLOSE_SUCESS = 0x00
LINK_CLOSE_TIMEOUT = 0x01
LINK_CLOSE_FAIL = 0x02


class ProvisioningBearerADVPDU(PDU):

    def __init__(self, link_id: int, transaction_number: int, payload: bytes):
        super().__init__(int(link_id).to_bytes(4, 'big') + int(transaction_number).to_bytes(1, 'big') + payload)


class ProvisioningBearerADVSocket(ProvisioningBearerSocket):

    def __init__(self, device_uuid: bytes, dongle_port: str):
        super().__init__(device_uuid, dongle_port)

        self.__link_id = None
        self.__transaction_number = None
        self.__close_reason = None

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

            # TODO: Start a timer. If this time reach to X seconds, then send a close with timeout

    def close(self):
        super().close()

        with DongleSocket(self._dongle_port, 115200) as socket:
            pbadv_pdu = ProvisioningBearerADVPDU(self.__link_id, next(self.__transaction_number),
                                                 payload=(b'\x0B' + self.__close_reason))
            dongle_pdu = DonglePDU(prov_bearer=PB_ADV, payload=pbadv_pdu.value)

            socket.write(dongle_pdu)

            # TODO: Stop all timers

    def write(self, payload: PDU):
        super().write(payload)

        with DongleSocket(self._dongle_port, 115200) as socket:
            tr_number = next(self.__transaction_number)

            for segment in self.__segment_payload(payload.value):
                pbadv_pdu = ProvisioningBearerADVPDU(self.__link_id, tr_number, segment)
                dongle_pdu = DonglePDU(prov_bearer=PB_ADV, payload=pbadv_pdu.value)

                socket.write(dongle_pdu)

    # TODO: Implement it
    async def read(self):
        super().read()

        raise NotImplemented
