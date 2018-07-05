#!/usr/bin/python3
import math

from core.shared_id_pool import SharedIDPool
from core.provisioning_link import *


class InvalidParameterType(Exception):

    def __init__(self, wrong_param_type, correct_param_types, position):
        self.wrong_param_type = wrong_param_type
        self.correct_param_types = correct_param_types
        self.position = position


class PBADVPDU:

    def __init__(self, link_id, transaction_number, payload):
        self.link_id = int(link_id).to_bytes(4, byteorder='big')
        self.transaction_number = int(transaction_number).to_bytes(1, byteorder='big')
        self.payload = bytes(payload)

    def __str__(self):
        return "{}|{}|{}".format(self.link_id, self.transaction_number, self.payload)

    def to_bytes(self):
        return self.link_id + self.transaction_number + self.payload


# TODO: Create a method to handle an incoming close message
# TODO: Create a method to wait the ack response. Send close case not ack has been arise
class PBADV:

    def __init__(self, write_cb, read_cb):
        self.write_cb = write_cb
        self.read_cb = read_cb
        self.link_ids = SharedIDPool(0xFFFFFFFF)
        self.links = []
        self.MTU_SIZE = 24

    def open(self, device_uuid: bytes):
        # Creating a new link
        link = ProvisioningLink(self.link_ids.get_new_id(), device_uuid, is_provisioner=True)
        # Check if this link already is in use. This check is made by uuid
        if link in self.links:
            raise DuplicateUUIDError(link)
        # If the link is not duplicate, then store it for further checks
        self.links.append(link)

        # Creating the Link Open payload
        link_open_payload = int(LINK_OPEN).to_bytes(1, 'big') + link.get_device_uuid()
        # Creating the Link Open PDU. This PDU will be send to device with uuid specified in method's parameter
        pdu = PBADVPDU(link.get_link_id(), link.get_a_transaction_number(), link_open_payload)
        # Sending Link Open PDU
        self.write_cb(pdu.to_bytes())
        # Return the link created
        return link

    def close(self, link: ProvisioningLink, reason: int):
        # If the link isn't stored, then raise a exception
        if link not in self.links:
            raise LinkNotFoundError(link)
        self.links.remove(link)

        # Creating the Link Close payload
        link_close_payload = int(LINK_CLOSE).to_bytes(1, 'big') + int(reason).to_bytes(1, 'big')
        # Creating the Link Close PDU. This PDU will be send to device with uuid specified on link
        pdu = PBADVPDU(link.get_link_id(), link.get_a_transaction_number(), link_close_payload)
        # Sending Link Close PDU
        self.write_cb(pdu.to_bytes())

    def write(self, payload: bytes, link: ProvisioningLink):
        for segment in self.segment_payload(payload):
            pdu = PBADVPDU(link.get_link_id(), link.get_a_transaction_number(), segment)
            self.write_cb(pdu.to_bytes())

    # TODO: Implement
    def read(self):
        raise NotImplemented

    def segment_payload(self, payload):
        payload_length = len(payload)

        if payload_length > self.MTU_SIZE:
            last_seg_number = int(math.ceil(payload_length / self.MTU_SIZE))

            for x in range(0, last_seg_number):
                yield payload[:self.MTU_SIZE]
                payload = payload[self.MTU_SIZE:]
        else:
            yield payload
