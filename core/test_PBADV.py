from unittest import TestCase
from core.pb_adv import PBADV
from core.provisioning_link import ProvisioningLink

def do_nothing():
    pass


def do_nothing_with_param(data: bytes):
    pass


class TestPBADV(TestCase):
    def test_open(self):
        pdu_result = None

        def store(data: bytes):
            pdu_result = data

        pb_result = PBADV(store, do_nothing)
        pb_expected = PBADV(store, do_nothing)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        pb_result.open(device_uuid)
        link_id = pb_result.link_ids.dirty_ids.get_nowait()

        pb_expected.links = ProvisioningLink(link_id, device_uuid, is_provisioner=True)
        pdu_expected = int(link_id).to_bytes(4, 'big') + b'\x00\x03' + device_uuid

        self.assertEqual(pb_result.links, pb_expected.links)
        self.assertEqual(pdu_result, pdu_expected)

    def test_close(self):
        self.fail()

    def test_write(self):
        self.fail()

    def test_read(self):
        self.fail()

    def test_segment_payload_big_payload(self):
        pb = PBADV(do_nothing, do_nothing)
        pb.MTU_SIZE = 3
        payload = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14'
        result = []
        expected = [b'\x32\x81\x52', b'\x7c\x3b\x6f', b'\x56\x64\x6c', b'\x0b\xcf\x93', b'\x22\x14']

        for segment in pb.segment_payload(payload):
            result.append(segment)

        self.assertEqual(result, expected, 'Expected: {}\nResult: {}\n'.format(expected, result))

    def test_segment_payload_small_payload(self):
        pb = PBADV(do_nothing, do_nothing)
        pb.MTU_SIZE = 3
        payload = b'\x32\x81\x52'
        result = []
        expected = [b'\x32\x81\x52']

        for segment in pb.segment_payload(payload):
            result.append(segment)

        self.assertEqual(result, expected, 'Expected: {}\nResult: {}\n'.format(expected, result))
