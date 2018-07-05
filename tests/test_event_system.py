from unittest import TestCase
from core.event_system import Event, Subscriber


class CustomSub(Subscriber):

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.buffer = []

    def notify(self, data: bytes):
        self.buffer.append(data)


class TestEventSystem(TestCase):

    def test_notify(self):
        s1 = CustomSub('s1')
        s2 = CustomSub('s2')
        e = Event()

        s1.subscribe(e)
        s2.subscribe(e)
        e.notify(b'\x57\x6f\x72\x6b\x69\x6e\x67')

        self.assertEqual([b'\x57\x6f\x72\x6b\x69\x6e\x67'], s1.buffer)
        self.assertEqual([b'\x57\x6f\x72\x6b\x69\x6e\x67'], s2.buffer)
