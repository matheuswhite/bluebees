#!/usr/bin/python3


class TransactionNumber:

    def __init__(self, is_provisioner=True):
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
