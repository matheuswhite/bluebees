from unittest import TestCase


class SerialMock:

    def __init__(self, msg_type: bytes):
        self.read_content = [
            f'@{msg_type} {content} {addr}'.encode('utf-8')
        ]
        self.read_index = -1
        self.write_content = []

    def open(self):
        pass

    def close(self):
        pass

    def readline(self):
        self.read_index += 1
        if self.read_index >= len(self.read_content):
            self.read_index = 0
        return self.read_content[self.read_index]

    def write(self, data: bytes):
        self.write_content.append(data)


class TestDongleDriver(TestCase):

    def test_send(self):
        self.fail('Not Implemented')

    def test_recv_prov(self):
        self.fail('Not Implemented')

    def test_recv_beacon(self):
        self.fail('Not Implemented')
