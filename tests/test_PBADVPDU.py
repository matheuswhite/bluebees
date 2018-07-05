from unittest import TestCase
from core.pb_adv import PBADVPDU


class TestPBADVPDU(TestCase):

    def test_to_bytes_with_payload_list(self):
        pdu = PBADVPDU(0x124BF8C7, 0x02, [0x23, 0x12, 0xab])
        result = pdu.to_bytes()
        expected = b'\x12\x4b\xF8\xC7\x02\x23\x12\xab'
        self.assertEqual(expected, result)

    def test_to_bytes_with_payload_bytes(self):
        pdu = PBADVPDU(0x124BF8C7, 0x02, bytes([0x23, 0x12, 0xab]))
        result = pdu.to_bytes()
        expected = b'\x12\x4b\xF8\xC7\x02\x23\x12\xab'
        self.assertEqual(expected, result)
