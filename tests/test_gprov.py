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
        self.fail('Not Implemented')

    def test_recv_transaction(self):
        self.fail('Not Implemented')
