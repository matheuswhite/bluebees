from core.utils import threaded, timeit
from core.link import Link
from core.transaction import Transaction
from layers.dongle import DongleDriver
from threading import Event
from time import time, sleep


class TransactionAckTimeout(Exception):
    pass


class LinkAckTimeout(Exception):
    pass


# TODO: Create a decorator to check if link is open on each method's step
class Gprov:

    def __init__(self, dongle_driver, start_taks=True):
        self.driver = dongle_driver
        self.link = Link()
        self.cache = []
        self.recv_transactions = []

        self.tr_ack_event = Event()
        self.link_ack_event = Event()
        self.link_close_event = Event()

        self.tr_retransmit_delay = 0.5
        self.link_open_retransmit_delay = 0.5

        if start_taks:
            self.recv_task()
            self.clean_cache_task()

    def get_transaction(self):
        while len(self.recv_transactions) == 0:
            pass
        tr = self.recv_transactions[0]
        self.recv_transactions = self.recv_transactions[1:]
        return tr

    def send_transaction(self, content: bytes):
        elapsed_time = 0

        while not self.tr_ack_event.is_set() and elapsed_time < 30:
            self.__atomic_send(content=content, elapsed_time=elapsed_time)

        if elapsed_time >= 30:
            self.close_link(b'\x01')
            raise TransactionAckTimeout()

        self.tr_ack_event.clear()

    def open_link(self, device_uuid: bytes):
        if self.link.is_open:
            return

        elapsed_time = 0
        self.link.device_uuid = device_uuid

        while not self.link_ack_event.is_set() and elapsed_time < 30:
            self.__atomic_link_open(elapsed_time=elapsed_time)

        if elapsed_time >= 30:
            raise LinkAckTimeout()

        self.link_ack_event.clear()
        self.link.is_open = True

    def close_link(self, reason: bytes):
        if not self.link.is_open:
            return

        self.driver.send(2, 20, self.link.get_adv_header() + b'\x0b' + reason)
        self.link.is_open = False

    @threaded
    def recv_task(self):
        pass

    @threaded
    def clean_cache_task(self):
        pass

    def send_transaction_ack(self):
        self.driver.send(2, 20, self.link.get_adv_header() + b'\x01')

    def check_link_close(self):
        # used in @ref recv_task
        pass

    def check_link_ack(self):
        # used in @ref recv_task
        pass

    def check_transaction_ack(self):
        # used in @ref recv_task
        pass

    @timeit
    def __atomic_send(self, **kwargs):
        tr = Transaction(kwargs['content'])
        for seg in tr.segments():
            self.driver.send(2, 20, self.link.get_adv_header() + seg)
        sleep(self.tr_retransmit_delay)

    @timeit
    def __atomic_link_open(self, **kwargs):
        self.driver.send(2, 20, self.link.get_adv_header() + b'\x03' + self.link.device_uuid)
        sleep(self.link_open_retransmit_delay)
