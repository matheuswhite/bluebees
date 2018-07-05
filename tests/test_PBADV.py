from unittest import TestCase
from core.pb_adv import PBADV
from core.provisioning_link import *

pdu_results = []


def store(data: bytes):
    global pdu_results
    pdu_results.append(data)


def do_nothing():
    pass


def do_nothing_with_param(data: bytes):
    pass


class TestPBADV(TestCase):
    def test_open(self):
        global pdu_results
        pdu_results = []

        pb_result = PBADV(store, do_nothing)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x00\x03' + device_uuid

        self.assertEqual([link], pb_result.links)
        self.assertEqual(pdu_expected, pdu_results[0])

    def test_close_sucess(self):
        global pdu_results
        pdu_results = []

        pb_result = PBADV(store, do_nothing)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)
        pb_result.close(link, LINK_CLOSE_SUCESS)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x01\x0b\x00'

        self.assertEqual([], pb_result.links)
        self.assertEqual(pdu_expected, pdu_results[1])

    def test_close_timeout(self):
        global pdu_results
        pdu_results = []

        pb_result = PBADV(store, do_nothing)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)
        pb_result.close(link, LINK_CLOSE_TIMEOUT)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x01\x0b\x01'

        self.assertEqual([], pb_result.links)
        self.assertEqual(pdu_expected, pdu_results[1])

    def test_close_fail(self):
        global pdu_results
        pdu_results = []

        pb_result = PBADV(store, do_nothing)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)
        pb_result.close(link, LINK_CLOSE_FAIL)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x01\x0b\x02'

        self.assertEqual([], pb_result.links)
        self.assertEqual(pdu_expected, pdu_results[1])

    def test_write(self):
        global pdu_results
        pdu_results = []

        pb = PBADV(store, do_nothing)
        pb.MTU_SIZE = 3
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'
        payload = b'\x2d\x9a\x91\x69\x9f\x61\x6e\x06'

        link = pb.open(device_uuid)
        pb.write(payload, link)

        link_id = int(link.link_id).to_bytes(4, 'big')
        pdu_expecteds = [
            link_id + b'\x00\x03' + device_uuid,
            link_id + b'\x01' + b'\x2d\x9a\x91',
            link_id + b'\x02' + b'\x69\x9f\x61',
            link_id + b'\x03' + b'\x6e\x06'
        ]

        self.assertEqual([link], pb.links)
        self.assertEqual(pdu_expecteds, pdu_results)

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

        self.assertEqual(expected, result)

    def test_segment_payload_small_payload(self):
        pb = PBADV(do_nothing, do_nothing)
        pb.MTU_SIZE = 3
        payload = b'\x32\x81\x52'
        result = []
        expected = [b'\x32\x81\x52']

        for segment in pb.segment_payload(payload):
            result.append(segment)

        self.assertEqual(expected, result)
