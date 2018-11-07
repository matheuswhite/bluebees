from unittest import TestCase
from layers.dongle import DongleDriver

# f'@{msg_type} {content} {addr}'.encode('utf-8')


class SerialMock:

    def __init__(self, read_content: list):
        self.read_content = read_content
        self.read_index = -1
        self.write_content = []
        self.temp_write = []
        self.erros = []
        self.is_open = False

    def open(self):
        if not self.is_open:
            self.is_open = True
        else:
            self.erros.append('Already Open')

    def close(self):
        if self.is_open:
            self.is_open = False
        else:
            self.erros.append('Not Open')

    def readline(self):
        if not self.is_open:
            self.erros.append('Not Open')
            return None

        self.read_index += 1
        if self.read_index >= len(self.read_content):
            self.read_index = 0
        return self.read_content[self.read_index]

    def write(self, data: bytes):
        if not self.is_open:
            self.erros.append('Not Open')
            return None

        self.temp_write.append(data)
        if data[-1:] == b'\n':
            content = b''
            for d in self.temp_write:
                content += d
            self.write_content.append(content)
            self.temp_write = []


class TestDongleDriver(TestCase):

    def test_send(self):
        read_content = [b'@beacon SGVscA== AA324251bf99\r\n']
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        # driver.dongle_communication_task()

        driver.send(2, 20, b'Help')

        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(0, len(ser.temp_write), 'Temp write count')
        self.assertEqual(1, len(ser.write_content), 'Write count')
        self.assertEqual(b'@prov 2 20 SGVscA==\r\n', ser.write_content[0])

    def test_send_25_bytes(self):
        self.fail('Not Implemented')

    def test_recv_prov(self):
        self.fail('Not Implemented')

    def test_recv_beacon(self):
        self.fail('Not Implemented')
