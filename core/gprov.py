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


class Gprov:

    def __init__(self, dongle_driver):
        self.driver = dongle_driver
        self.link = Link()
        self.cache = []
        self.recv_transactions = []

        self.tr_ack_event = Event()
        self.tr_ack_expected = 0x00
        self.link_ack_event = Event()
        self.link_close_event = Event()

        self.tr_retransmit_delay = 3
        self.link_open_retransmit_delay = 3
        self.clean_cache_delay = 30

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

        log.log('Sending transaction...')
        while not self.tr_ack_event.is_set() and elapsed_time < 30:
            self.__atomic_send(content=content, elapsed_time=elapsed_time)
            if self.link_close_event.is_set():
                self.link_close_event.clear()
                raise DeviceCloseLink()

        if elapsed_time >= 30:
            self.close_link(b'\x01')
            raise TransactionAckTimeout()

        # log.succ('Transaction ack received')
        self.tr_ack_event.clear()

    def open_link(self, device_uuid: bytes):
        if self.link.is_open:
            return

        elapsed_time = 0
        self.link.device_uuid = device_uuid

        log.log('Sending open...')
        while not self.link_ack_event.is_set() and elapsed_time < 30:
            self.__atomic_link_open(elapsed_time=elapsed_time)

        if elapsed_time >= 30:
            raise LinkAckTimeout()

        log.succ('Ack received')
        self.link_ack_event.clear()
        self.link.is_open = True

    def close_link(self, reason: bytes):
        if not self.link.is_open:
            return

        self.driver.send(0, 20, self.link.get_adv_header() + b'\x0b' + reason)
        self.link.close_reason = reason
        self.link.is_open = False

    @threaded
    def recv_task(self):
        tr = Transaction()
        dev_link = Link(self.link.link_id)

        while True:
            log.dbg('Recv msgs...')
            msg = self.driver.recv('prov')
            link_id = int.from_bytes(msg[0:4], 'big')
            dev_tr_number = msg[4]
            segment = msg[5:]

            # log.dbg(f'Link_id: {msg[0:4]}, dev_tr_num: {msg[4]}, seg: {segment}')

            if segment[0] == 0x0b:
                self.link.is_open = False
                self.link.close_reason = segment[1]
                self.link_close_event.set()
                yield_()
                continue
            elif segment[0] == 0x07:
                # log.succ('Link Ack Recognized')
                self.link_ack_event.set()
                yield_()
                continue
            elif segment[0] == 0x01 and dev_tr_number == self.tr_ack_expected:
                log.succ(f'Tr Ack Recognized: {dev_tr_number}/{self.tr_ack_expected}')
                self.tr_ack_event.set()
                yield_()
                continue

            # if self.link.link_id != link_id:
            #     continue
            # else:
            #     log.dbg('link same')

            # if dev_link.device_transaction_number != dev_tr_number:
            #     log.wrn(f'Wrong device number. Received {dev_tr_number} instead of '
            #             f'{dev_link.device_transaction_number}')

            log.dbg(b'Message received: ' + segment[5:])

            tr.add_recv_segment(segment)
            transaction, err_msg = tr.get_recv_transaction()
            if transaction is None:
                log.wrn(f'Err msg: {err_msg}')
                yield_()
                continue

            self.send_transaction_ack(dev_link)

            if transaction in self.cache:
                yield_()
                continue

            self.cache.append(transaction)
            self.recv_transactions.append(transaction)
            tr = Transaction()
            dev_link.increment_device_transaction_number()

            yield_()

    @threaded
    def clean_cache_task(self):
        while True:
            sleep(self.clean_cache_delay)
            self.cache = []

    def send_transaction_ack(self, link: Link):
        self.driver.send(2, 20, link.get_adv_header() + b'\x01')

    @timeit
    def __atomic_send(self, **kwargs):
        self.tr_ack_expected = self.link.transaction_number
        tr = Transaction(kwargs['content'])
        for seg in tr.segments():
            log.log(b'Header: ' + self.link.get_adv_header() + b', Send: ' + seg)
            self.driver.send(0, 20, self.link.get_adv_header() + seg)
        sleep(self.tr_retransmit_delay)

    @timeit
    def __atomic_link_open(self, **kwargs):
        log.log(b'Send: ' + self.link.get_adv_header() + b'\x03' + self.link.device_uuid)
        self.driver.send(0, 20, self.link.get_adv_header() + b'\x03' + self.link.device_uuid)
        sleep(self.link_open_retransmit_delay)
