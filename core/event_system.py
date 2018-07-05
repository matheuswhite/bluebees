#!/usr/bin/python3
"""
The subscriber can subscribe, for now, in one event
"""
# TODO: Increase the number of event subscriptions allowed for Subscriber


class Event:

    def __init__(self):
        self.subscribers = []

    def notify(self, data: bytes):
        for subscriber in self.subscribers:
            subscriber.notify(data)


class Subscriber:

    def __init__(self):
        self.events = []

    def notify(self, data: bytes):
        pass

    def subscribe(self, event: Event):
        self.events.append(event)
        event.subscribers.append(self)
