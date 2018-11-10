from unittest import TestCase
from layers.gprov import GProvLayer, CLOSE_SUCCESS, CLOSE_TIMEOUT, CLOSE_FAIL,UnexpectedDeviceCloseException
from layers.pb_adv import PbAdvLayer
from layers.dongle import DongleDriver
from tests.serial_mock import SerialMock
from core.link import Link
import time
import base64


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = (te - ts)
        else:
            print(f'{method.__name__} {(te - ts)} ms')
        return result
    return timed


class TestGProv(TestCase):

    def test_open(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x00') + b' AA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x02') + b' BA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x07') + b' CA435699BD01\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        @timeit
        def gprov_open(**kwargs):
            return gprov.open(kwargs.get('link'))

        logtime_data = {}
        gprov_open(log_time=logtime_data, link=link)

        content = link.link_id.to_bytes(4, 'big') + b'\x00\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'

        self.assertLessEqual(logtime_data['gprov_open'.upper()], 30, 'Execution Time check')
        self.assertTrue(link.is_open, 'Link open flag check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message send '
                                                                                                     'check')

    def test_close_sucess(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x00') + b' AA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x02') + b' BA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x07') + b' CA435699BD01\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        gprov.open(link)
        link.close_reason = CLOSE_SUCCESS
        gprov.close(link)

        content = link.link_id.to_bytes(4, 'big') + b'\x00\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'
        content2 = link.link_id.to_bytes(4, 'big') + b'\x01\x0B\x00'

        self.assertFalse(link.is_open, 'Link open flag check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message open '
                                                                                                     'send check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content2) + b'\r\n', ser.write_content[1], 'Message close '
                                                                                                      'send check')

    def test_close_timeout(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x00') + b' AA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x02') + b' BA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x07') + b' CA435699BD01\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        gprov.open(link)
        link.close_reason = CLOSE_TIMEOUT
        gprov.close(link)

        content = link.link_id.to_bytes(4, 'big') + b'\x00\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'
        content2 = link.link_id.to_bytes(4, 'big') + b'\x01\x0B\x01'

        self.assertFalse(link.is_open, 'Link open flag check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message open '
                                                                                                     'send check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content2) + b'\r\n', ser.write_content[1], 'Message close '
                                                                                                      'send check')

    def test_close_fail(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x00') + b' AA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x02') + b' BA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x07') + b' CA435699BD01\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        gprov.open(link)
        link.close_reason = CLOSE_FAIL
        gprov.close(link)

        content = link.link_id.to_bytes(4, 'big') + b'\x00\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'
        content2 = link.link_id.to_bytes(4, 'big') + b'\x01\x0B\x02'

        self.assertFalse(link.is_open, 'Link open flag check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message open '
                                                                                                     'send check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content2) + b'\r\n', ser.write_content[1], 'Message close '
                                                                                                      'send check')

    def test_unexpected_device_close(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x07') + b' AA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x01\x04\x00\x05\x08\xAE') + b' CA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x02\x0B\x02') + b' CA435699BD01\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        gprov.open(link)

        with self.assertRaises(UnexpectedDeviceCloseException) as context:
            _ = gprov.recv(link)

        content = link.link_id.to_bytes(4, 'big') + b'\x00\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'

        self.assertFalse(link.is_open, 'Link open flag check')
        self.assertEqual(b'\x02', context.exception.close_reason)
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message open '
                                                                                                     'send check')

    def test_unexpected_device_close_2nd_case(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x00\x07') + b' AA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae\x01\x0B\x02') + b' CA435699BD01\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        gprov.open(link)

        with self.assertRaises(UnexpectedDeviceCloseException) as context:
            gprov.send(link, b'Help1Help2Help3Help4Help5Help6Help7Help8Help9Help0')

        content = link.link_id.to_bytes(4, 'big') + b'\x00\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'

        self.assertFalse(link.is_open, 'Link open flag check')
        self.assertEqual(b'\x02', context.exception.close_reason)
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message open '
                                                                                                     'send check')

    def test_send_transaction(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae' + b'\x00' + b'\x07') + b' CA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae' + b'\x01' + b'\x01') + b' DA435699BD01\r\n'
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        gprov.open(link)

        send_content = b'Help1Help2Help3Help4HelZHelp1Help2Help3Help4HelWHelp5Help6Help7'
        gprov.send(link, send_content)

        content = link.link_id.to_bytes(4, 'big') + b'\x00' + b'\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'
        content2 = link.link_id.to_bytes(4, 'big') + b'\x01' + b'\x08' + b'\x00\x3F' + b'\x1a' + b'Help1Help2Help3' \
                                                                                                 b'Help4'
        content3 = link.link_id.to_bytes(4, 'big') + b'\x01' + b'\x06' + b'HelZHelp1Help2Help3Help'
        content4 = link.link_id.to_bytes(4, 'big') + b'\x01' + b'\x0A' + b'4HelWHelp5Help6Help7'

        self.assertTrue(link.is_open, 'Link open flag check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message open '
                                                                                                     'send check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content2) + b'\r\n', ser.write_content[1], 'Message send '
                                                                                                      'start check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content3) + b'\r\n', ser.write_content[2], 'Message send '
                                                                                                      'continuation 1 '
                                                                                                      'check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content4) + b'\r\n', ser.write_content[3], 'Message send '
                                                                                                      'continuation 2 '
                                                                                                      'check')

    def test_recv_transaction(self):
        prefix = b'@prov '
        read_content = [
            prefix + base64.b64encode(b'\x00\x00\x12\xae' + b'\x00' + b'\x07') + b' CA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae' + b'\x83' + b'\x08' + b'\x00\x3F' + b'\x1a' + b'Help1Help2'
                                                                                                        b'Help3Help4')
            + b' DA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae' + b'\x83' + b'\x06' + b'HelZHelp1Help2Help3Help')
            + b' EA435699BD01\r\n',
            prefix + base64.b64encode(b'\x00\x00\x12\xae' + b'\x83' + b'\x0A' + b'4HelWHelp5Help6Help7')
            + b' FA435699BD01\r\n',
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)
        pb_adv = PbAdvLayer(driver)
        gprov = GProvLayer(pb_adv)
        link = Link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD')

        driver.dongle_communication_task()

        gprov.open(link)
        content_recv = gprov.recv(link)

        content = link.link_id.to_bytes(4, 'big') + b'\x00' + b'\x03' \
                                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xDD'
        content2 = link.link_id.to_bytes(4, 'big') + b'\x83' + b'\x01'

        self.assertTrue(link.is_open, 'Link open flag check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content) + b'\r\n', ser.write_content[0], 'Message open '
                                                                                                     'send check')
        self.assertEqual(b'@prov 2 20 ' + base64.b64encode(content2) + b'\r\n', ser.write_content[1], 'Message recv '
                                                                                                      'ack check')
        self.assertEqual(b'Help1Help2Help3Help4HelZHelp1Help2Help3Help4HelWHelp5Help6Help7', content_recv)
