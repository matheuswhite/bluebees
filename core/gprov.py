from core.utils import threaded, timeit
from core.link import Link
from core.transaction import Transaction
from threading import Event
from time import sleep
from core.log import Log
from core.scheduling import scheduler, TaskTimer
from core.utils import crc8
from core.dongle import MAX_MTU


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


class DeviceConnection:

    def __init__(self, link_id):
        self.link_id = link_id
        self.prov_tr_number = 0x00
        self.device_tr_number = 0x80
        self.recv_transactions = []
        self.messages = {}
        self.cache = []
        self.tr_status = 'start'
        self.fcs = 0
        self.tr_len = 0
        self.segn = 0
        self.clear_cache_timeout = 30
        self.is_alive = True

        scheduler.spawn_task(f'clear_cache_task{link_id}', self._clear_cache_task)

    def _clear_cache_task(self):
        while self.is_alive:
            clear_timer = TaskTimer()
            clear_timer.timeout = self.clear_cache_timeout
            scheduler.wait_timer(f'_clear_cache_task{self.link_id}', clear_timer)
            yield
            self.cache = []

    def _get_last_transaction_task(self):
        while len(self.recv_transactions) == 0:
            yield
        last_recv_transaction = self.recv_transactions[0]
        self.recv_transactions = self.recv_transactions[1:]
        yield last_recv_transaction

    def _is4me(self, content: bytes):
        return content[0:4] == int(self.link_id).to_bytes(4, 'big')

    def _already_in_cache(self, content: bytes):
        return content in self.cache

    def _is_tr_ack(self, content: bytes):
        return content[4] == self.prov_tr_number and content[5] == 0x01

    def _has_correct_tr_number(self, content: bytes):
        return content[4] == self.device_tr_number

    def _validate_message(self):
        # remount transaction
        tr_content = b''
        x = 0
        while self.messages:
            tr_content += self.messages[x]
            del self.messages[x]
            x += 1

        # check total length
        if self.tr_len != len(tr_content):
            return

        # check fcs
        calc_fcs = crc8(tr_content)
        if self.fcs != calc_fcs:
            return

        # add transaction
        self.recv_transactions.append(tr_content)

        self.tr_status = 'start'

    def add_recv_message(self, content: bytes):
        if not self._is4me(content):
            return
        if self._already_in_cache(content):
            return
        if self._is_tr_ack(content):
            self.prov_tr_number += 1
            return
        if not self._has_correct_tr_number(content):
            return

        content = content[5:]

        if self.tr_status == 'start':
            first_byte = content[0]
            if first_byte & 0x03 != 0:
                return

            self.segn = (first_byte & 0xfc) >> 2
            self.tr_len = int.from_bytes(content[1:3], 'big')
            self.fcs = content[3]
            self.messages[0] = content[4:]
        elif self.tr_status == 'continuation':
            first_byte = content[0]
            if first_byte & 0x03 != 2:
                self.tr_status = 'start'
                return

            seg_index = (first_byte & 0xfc) >> 2
            self.messages[seg_index] = content[1:]

        if len(self.messages) - 1 < self.segn:
            self.tr_status = 'continuation'
        else:
            self._validate_message()

        self.cache.append(content)

    # def _usage_task(self):
    #     msgs = device_conn.mount_snd_transaction(b'')
    #     for m in msgs:
    #         driver.send(m)
    #
    #     ret = []
    #     device_conn.get_last_transaction('_usage', ret)
    #     yield
    #
    #     content = ret[0]

    def get_last_transaction_task(self, invoker_name: str, ret_queue: list):
        spawned_task_name = f'_get_last_transaction_task{self.link_id}'
        scheduler.spawn_task(spawned_task_name, self._get_last_transaction_task(), ret_queue)
        scheduler.set_dependency(invoker_name, spawned_task_name)

    def mount_snd_transaction(self, content: bytes):
        messages = []

        if len(content) == 0:
            return messages

        header = int(self.link_id).to_bytes(4, 'big') + int(self.prov_tr_number).to_bytes(1, 'big')

        # start message
        total_seg_number = int((len(content) - 1)/MAX_MTU)
        segn = (total_seg_number << 2).to_bytes(1, 'big')
        total_length = len(content).to_bytes(2, 'big')
        fcs = crc8(content).to_bytes(1, 'big')
        has_continuation = total_length > MAX_MTU
        if has_continuation:
            data = content[0:MAX_MTU]
            content = content[MAX_MTU:]
        else:
            data = content
        messages.append(header + segn + total_length + fcs + data)

        # continuation messages
        if has_continuation:
            for i in range(1, total_seg_number):
                seg_index = ((i << 2) | 0x02).to_bytes(1, 'big')
                data = content[0:MAX_MTU]
                content = content[MAX_MTU:]
                messages.append(header + seg_index + data)
            seg_index = ((total_seg_number << 2) | 0x02).to_bytes(1, 'big')
            messages.append(header + seg_index + content)

        return messages

    # TODO
    def open_connection(self):
        raise NotImplementedError

    # TODO
    def close_connection(self):
        raise NotImplementedError


class GenericProvisioner:

    def __init__(self, dongle_driver):
        self.driver = dongle_driver
        self.connections = []

