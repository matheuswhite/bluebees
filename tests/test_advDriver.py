from unittest import TestCase
from core.adv import AdvDriver
from tests.SerialTestHelper import SerialTestHelper
from time import sleep


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
        self.fail()

    def test_read(self):
        self.fail()

    def test_read_in_background(self):
        self.fail()

    def test_threaded(self):
        helper0 = SerialTestHelper('/dev/ttyACM0')
        helper0.listen()

        expected = b'\x48\x65\x6c\x70'

        helper0.push_message('@reply', expected)
        sleep(5)

        result = helper0.pop_message('@reply')

        self.assertEqual(result, expected)
