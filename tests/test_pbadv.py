from unittest import TestCase
from layers.pb_adv import PbAdvLayer
from layers.dongle import DongleDriver, MaxTriesException
from tests.serial_mock import SerialMock
from core.link import Link
import base64


class TestPbAdvLayer(TestCase):

    def test_send(self):
        read_content = [
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        pb_adv.send(link, b'Help')

        content = link.link_id.to_bytes(4, 'big') + b'\x00Help'
        content = base64.b64encode(content).decode('utf-8')
        self.assertEqual(f'@prov 2 20 {content}\r\n'.encode('utf-8'), ser.write_content[0])

    def test_send_max_length(self):
        read_content = [
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        pb_adv.send(link, b'Help0Help1Help2Help3Help')

        content = link.link_id.to_bytes(4, 'big') + b'\x00Help0Help1Help2Help3Help'
        content = base64.b64encode(content).decode('utf-8')
        self.assertEqual(f'@prov 2 20 {content}\r\n'.encode('utf-8'), ser.write_content[0])

    def test_send_max_length_plus_1(self):
        read_content = [
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        with self.assertRaises(Exception) as context:
            pb_adv.send(link, b'Help0Help1Help2Help3Help5')

        self.assertTrue('Message length greater than 24 bytes' in str(context.exception))

    def test_recv(self):
        read_content = [
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)

        driver.dongle_communication_task()

        content = pb_adv.recv()
        content2 = pb_adv.recv()

        self.assertEqual(b'Help', content)
        self.assertEqual(b'Help2', content2)

    def test_recv_limited_tries(self):
        read_content = [
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)

        driver.dongle_communication_task()

        content = pb_adv.recv()

        content2 = pb_adv.recv(tries=3, interval=0.5)

        self.assertIsNone(content2)
        self.assertEqual(b'Help', content)

    def test_send_n_recv(self):
        read_content = [
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxw AA324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n',
            b'@prov AAABrABIZWxwMg== BB324251bf99\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        pb_adv.send(link, b'Help')
        content = pb_adv.recv()
        content2 = pb_adv.recv()

        contentb64 = link.link_id.to_bytes(4, 'big') + b'\x00Help'
        contentb64 = base64.b64encode(contentb64).decode('utf-8')
        self.assertEqual(f'@prov 2 20 {contentb64}\r\n'.encode('utf-8'), ser.write_content[0])
        self.assertEqual(b'Help', content)
        self.assertEqual(b'Help2', content2)
