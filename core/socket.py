#!/usr/bin/python3
from core.event_system import Event


class Socket:

    def __init__(self):
        self.new_data_event = Event()

    def write(self, data: bytes):
        pass
