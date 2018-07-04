#!/usr/bin/python3
"""
This class represent a link. So, it must be created in every link establishment and destroyed at end of link.
"""

# PROVISIONING_BEARER_CONTROL_CODE = 0b11
# PROVISIONING_BEARER_CONTROL_MASK = 0x03
# BEARER_OPCODE_MASK = 0xFC
LINK_OPEN = 0x00
LINK_ACK = 0x01
LINK_CLOSE = 0x02


class DuplicateUUIDError(Exception):

    def __init__(self, link):
        self.link = link


class TransactionNumberIterator:

    def __init__(self, is_provisioner):
        self.is_provisioner = is_provisioner
        if self.is_provisioner:
            self.start = 0x00
            self.end = 0x7F
        else:
            self.start = 0x80
            self.end = 0xFF
        self.current = self.start

    def __iter__(self):

        return self

    def __next__(self):
        out = self.current
        if self.current == self.end:
            self.current = self.start
        else:
            self.current += 1
        return out


class ProvisioningLink:

    def __init__(self, link_id, device_uuid, is_provisioner):
        self.link_id = link_id
        self.device_uuid = device_uuid
        self._is_provisioner = is_provisioner
        self._is_active = False
        self.tr_number_iter = TransactionNumberIterator(self._is_provisioner)

    def __eq__(self, other):
        return self.device_uuid == other.device_uuid

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.device_uuid)

    # TODO: To study @property flag
    def get_link_id(self):
        return self.link_id

    def get_device_uuid(self):
        return self.device_uuid

    def is_provisioner(self):
        return self._is_provisioner

    def is_active(self):
        return self._is_active

    def active(self):
        self._is_active = True

    def get_a_transaction_number(self):
        return next(self.tr_number_iter)
