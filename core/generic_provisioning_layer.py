#!/usr/bin/python3
from core.event_system import Event, Subscriber
from core.pb_adv import PBADV
from core.provisioning_link import *
from core.socket import Socket
from random import randrange
import math
from time import sleep

# TODO: Move the link management to this layer
# TODO: Test the time between writes
# TODO: Add FCS calc algorithm


TRANSACTION_START = 0b00
TRANSACTION_ACK = 0b01
TRANSACTION_CONTINUATION = 0b10
PROVISION_BEARER_CONTROL = 0b11


class GenericProvisioningPDU:

    def __init__(self, control, payload):
        self.control = control
        self.payload = payload

    def to_bytes(self):
        return self.control + self.payload


class TransactionStartPDU(GenericProvisioningPDU):

    def __init__(self, last_segment_number, fcs, data):
        self.last_segment_number = last_segment_number
        self.fcs = fcs
        self.data = data

        super().__init__(int(self.last_segment_number >> 2 | TRANSACTION_START).to_bytes(1, 'big') +
                         int(len(data)).to_bytes(2, 'big') +
                         int(fcs).to_bytes(1, 'big'),
                         data)


class TransactionAckPDU(GenericProvisioningPDU):

    def __init__(self):
        super().__init__(int(TRANSACTION_ACK).to_bytes(1, 'big'), b'')


class TransactionContinuationPDU(GenericProvisioningPDU):

    def __init__(self, segment_index, data):
        self.segment_index = segment_index

        super().__init__(int(self.segment_index >> 2 | TRANSACTION_CONTINUATION).to_bytes(1, 'big'), data)


class GenericProvisioningLayer(Subscriber):

    def __init__(self, socket: Socket, device_uuid: bytes):
        super().__init__()

        self.pb_adv = PBADV(socket)
        self.new_ppdu_event = Event()
        self.device_uuid = device_uuid
        self.MTU_SIZE = 81

    # TODO: Test it
    def write(self, payload: bytes):
        link = self.pb_adv.open(self.device_uuid)

        # waiting ack

        segments = self.segment_payload(payload)
        fcs = 0

        self.write_single(TransactionStartPDU(len(segments), fcs, segments[0]), link)

        for x in range(1, len(segments)):
            self.write_single(TransactionContinuationPDU(x, segments[x]), link)

        self.pb_adv.close(link, LINK_CLOSE_SUCESS)

    # TODO: Implement it
    def notify(self, data: bytes):
        raise NotImplemented

    # TODO: Test it
    def write_single(self, pdu, link):
        sleep_time = randrange(20, 50)/1000.0
        sleep(sleep_time)
        self.pb_adv.write(pdu.to_bytes(), link)

    # TODO: Test it
    def segment_payload(self, payload):
        payload_length = len(payload)
        segments = []

        if payload_length > self.MTU_SIZE:
            last_seg_number = int(math.ceil(payload_length / self.MTU_SIZE))

            for x in range(0, last_seg_number):
                segments.append(payload[:self.MTU_SIZE])
                payload = payload[self.MTU_SIZE:]
        else:
            segments.append(payload)

        return segments

    def get_new_ppdu_event(self):
        return self.new_ppdu_event
