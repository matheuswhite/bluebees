from core.utils import threaded, timeit
from core.link import Link
from core.transaction import Transaction
from threading import Event
from time import sleep
from core.log import Log


log = Log('Gprov')


class TransactionAckTimeout(Exception):
    pass


class LinkAckTimeout(Exception):
    pass


class DeviceCloseLink(Exception):
    pass


# TODO: Comment the code
class Gprov:

    def __init__(self, dongle_driver, start_taks=True):
        self.driver = dongle_driver
        self.link = Link()
        self.cache = []
        self.recv_transactions = []

        self.tr_ack_event = Event()
        self.link_ack_event = Event()
        self.link_close_event = Event()
        self.link_close_event.set()

        self.tr_retransmit_delay = 0.5
        self.link_open_retransmit_delay = 0.5
        self.clean_cache_delay = 35

        if start_taks:
            self.recv_task()
            self.clean_cache_task()

    def get_transaction(self):
        if self.link_close_event.is_set():
            self.link_close_event.clear()
            raise DeviceCloseLink()

        while len(self.recv_transactions) == 0:
            pass
        tr = self.recv_transactions[0]
        self.recv_transactions = self.recv_transactions[1:]
        return tr

    def send_transaction(self, content: bytes):
        elapsed_time = 0

        while not self.tr_ack_event.is_set() and elapsed_time < 30:
            if self.link_close_event.is_set():
                self.link_close_event.clear()
                raise DeviceCloseLink()
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
        self.link.close_reason = reason
        self.link.is_open = False

    @threaded
    def recv_task(self):
        tr = Transaction()
        dev_link = Link(self.link.link_id)

        while True:
            msg = self.driver.recv('prov')
            link_id = int.from_bytes(msg[0:4], 'big')
            dev_tr_number = msg[5]
            segment = msg[5:]

            if segment[0] == 0x0b:
                self.link.is_open = False
                self.link.close_reason = segment[1]
                self.link_close_event.set()
                continue
            if segment[0] == 0x07:
                self.link_ack_event.set()
                continue
            if segment == 0x01:
                self.tr_ack_event.set()
                continue

            if self.link.link_id != link_id:
                continue
            if dev_link.device_transaction_number != dev_tr_number:
                print(f'Wrong device number. Received {dev_tr_number} instead of {dev_link.device_transaction_number}')

            tr.add_recv_segment(segment)
            transaction, _ = tr.get_recv_transaction()
            if transaction is None:
                continue

            self.send_transaction_ack(dev_link)

            if transaction in self.cache:
                continue

            log.log('Recv: ' + transaction.decode('utf-8'))
            self.cache.append(transaction)
            self.recv_transactions.append(transaction)
            tr = Transaction()
            dev_link.increment_device_transaction_number()

    @threaded
    def clean_cache_task(self):
        while True:
            sleep(self.clean_cache_delay)
            self.cache = []

    def send_transaction_ack(self, link: Link):
        self.driver.send(2, 20, link.get_adv_header() + b'\x01')

    @timeit
    def __atomic_send(self, **kwargs):
        tr = Transaction(kwargs['content'])
        for seg in tr.segments():
            log.log('Send: ' + (self.link.get_adv_header() + seg).decode('utf-8'))
            self.driver.send(2, 20, self.link.get_adv_header() + seg)
        sleep(self.tr_retransmit_delay)

    @timeit
    def __atomic_link_open(self, **kwargs):
        log.log('Send: ' + (self.link.get_adv_header() + b'\x03' + self.link.device_uuid).decode('utf-8'))
        self.driver.send(2, 20, self.link.get_adv_header() + b'\x03' + self.link.device_uuid)
        sleep(self.link_open_retransmit_delay)
