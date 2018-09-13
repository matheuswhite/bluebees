from unittest import TestCase
from core.adv import AdvDriver


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