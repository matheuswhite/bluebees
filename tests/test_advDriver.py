from unittest import TestCase
from core.adv import AdvDriver
from serial import Serial
from random import randint
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

        payload = b'Help'

        expected1 = bytes('@prov 48656c70\r\n'.encode('utf8'))
        expected2 = bytes('@message 48656c70\r\n'.encode('utf8'))
        expected3 = bytes('@beacon 48656c70\r\n'.encode('utf8'))

        serial.open()
        adv.write(payload=payload, type_='prov', xmit=2, duration=200, endianness='big')
        result = serial.readline()
        self.assertEqual(expected1, result)
        print('Msg 1 done!')

        adv.write(payload=payload, type_='message', xmit=2, duration=200, endianness='big')
        result = serial.readline()
        self.assertEqual(expected2, result)
        print('Msg 2 done!')

        adv.write(payload=payload, type_='beacon', xmit=2, duration=200, endianness='big')
        result = serial.readline()
        self.assertEqual(expected3, result)
        print('Msg 3 done!')

        serial.close()

    def test_multiple_writes(self):
        settings = AdvSettings()
        settings.port = '/dev/ttyACM0'
        settings.baud_rate = 115200
        adv = AdvDriver()

        serial = Serial()
        serial.port = '/dev/ttyACM1'
        serial.baudrate = 115200
        serial.open()

        results = []
        expecteds = []

        samples = 10

        for x in range(samples):
            payload = bytes('Help{}'.format(randint(0, 255)).encode('utf8'))
            adv.write(payload=payload, type_='prov', xmit=2, duration=200, endianness='big')
            results.append(serial.readline())
            expecteds.append(bytes('@prov {}\r\n'.format(adv.bytes_to_hexstr(payload)).encode('utf8')))
            print('Msg {} done!'.format(x))

        serial.close()

        for x in range(samples):
            self.assertEqual(expecteds[x], results[x])

    def test_read(self):
        self.fail()

    def test_read_in_background(self):
        self.fail()
