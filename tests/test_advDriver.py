from unittest import TestCase
from core.adv import AdvDriver
from serial import Serial
from core.settings import AdvSettings


class TestAdvDriver(TestCase):

    def test_bytes_to_hexstr_big(self):
        driver = AdvDriver()
        msg = b'Help'
        expected = '48656c70'

        result = driver.bytes_to_hexstr(data=msg, endianness='big')

        self.assertEqual(result, expected)

    def test_bytes_to_hexstr_little(self):
        driver = AdvDriver()
        msg = b'Help'
        expected = '706c6548'

        result = driver.bytes_to_hexstr(data=msg, endianness='little')

        self.assertEqual(result, expected)

    def test_write(self):
        settings = AdvSettings()
        settings.port = '/dev/ttyACM0'
        settings.baud_rate = 115200

        adv = AdvDriver()
        serial = Serial()
        serial.port = '/dev/ttyACM1'
        serial.baudrate = 115200
        serial.open()
        for x in range(3):
            serial.readline()

        payload = b'Help'

        expected1 = bytes('@prov 48656c70\r\n'.encode('utf8'))
        expected2 = bytes('@message 48656c70\r\n'.encode('utf8'))
        expected3 = bytes('@beacon 48656c70\r\n'.encode('utf8'))

        adv.write(payload=payload, type_='prov', xmit=2, duration=200, endianness='big')
        result1 = serial.readline()

        adv.write(payload=payload, type_='message', xmit=2, duration=200, endianness='big')
        result2 = serial.readline()

        adv.write(payload=payload, type_='beacon', xmit=2, duration=200, endianness='big')
        result3 = serial.readline()

        serial.close()

        self.assertEqual(expected1, result1)
        self.assertEqual(expected2, result2)
        self.assertEqual(expected3, result3)

    def test_read(self):
        self.fail()

    def test_read_in_background(self):
        self.fail()
