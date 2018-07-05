from unittest import TestCase
from core.pb_adv import PBADV
from core.provisioning_link import *
from core.event_system import Event, Subscriber
from core.socket import Socket


class CustomSub(Subscriber):

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.buffer = []

    def notify(self, data: bytes):
        self.buffer.append(data)


class CustomSocket(Socket):

    def __init__(self):
        super().__init__()
        self.pdu_results = []

    def write(self, data: bytes):
        self.pdu_results.append(data)


class TestPBADV(TestCase):
    def test_open(self):
        socket = CustomSocket()
        pb_result = PBADV(socket)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x00\x03' + device_uuid

        self.assertEqual([link], pb_result.links)
        self.assertEqual(pdu_expected, socket.pdu_results[0])

    def test_close_sucess(self):
        socket = CustomSocket()
        pb_result = PBADV(socket)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)
        pb_result.close(link, LINK_CLOSE_SUCESS)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x01\x0b\x00'

        self.assertEqual([], pb_result.links)
        self.assertEqual(pdu_expected, socket.pdu_results[1])

    def test_close_timeout(self):
        socket = CustomSocket()
        pb_result = PBADV(socket)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)
        pb_result.close(link, LINK_CLOSE_TIMEOUT)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x01\x0b\x01'

        self.assertEqual([], pb_result.links)
        self.assertEqual(pdu_expected, socket.pdu_results[1])

    def test_close_fail(self):
        socket = CustomSocket()
        pb_result = PBADV(socket)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb_result.open(device_uuid)
        pb_result.close(link, LINK_CLOSE_FAIL)

        pdu_expected = int(link.link_id).to_bytes(4, 'big') + b'\x01\x0b\x02'

        self.assertEqual([], pb_result.links)
        self.assertEqual(pdu_expected, socket.pdu_results[1])

    def test_write(self):
        socket = CustomSocket()
        pb = PBADV(socket)
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
        self.assertEqual(pdu_expecteds, socket.pdu_results)

    def test_notify(self):
        s = CustomSub('s')
        socket = CustomSocket()
        pb = PBADV(socket)
        s.subscribe(pb.get_new_gppdu_event())

        socket.new_data_event.notify(b'\x57\x6f\x72\x6b\x82\x6e\x67')

        self.assertEqual(b'\x6e\x67', s.buffer[0])

    def test_remove_link_by_link_id(self):
        socket = CustomSocket()
        pb = PBADV(socket)
        device_uuid = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14\xff\xbb'

        link = pb.open(device_uuid)
        pb.remove_link_by_link_id(link.get_link_id())

        self.assertEqual([], pb.links)

    def test_segment_payload_big_payload(self):
        socket = CustomSocket()
        pb = PBADV(socket)
        pb.MTU_SIZE = 3
        payload = b'\x32\x81\x52\x7c\x3b\x6f\x56\x64\x6c\x0b\xcf\x93\x22\x14'
        result = []
        expected = [b'\x32\x81\x52', b'\x7c\x3b\x6f', b'\x56\x64\x6c', b'\x0b\xcf\x93', b'\x22\x14']

        for segment in pb.segment_payload(payload):
            result.append(segment)

        self.assertEqual(expected, result)

    def test_segment_payload_small_payload(self):
        socket = CustomSocket()
        pb = PBADV(socket)
        pb.MTU_SIZE = 3
        payload = b'\x32\x81\x52'
        result = []
        expected = [b'\x32\x81\x52']

        for segment in pb.segment_payload(payload):
            result.append(segment)

        self.assertEqual(expected, result)
