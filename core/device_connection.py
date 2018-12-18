from core.scheduling import scheduler, Timer
from core.utils import crc8
from core.dongle import MAX_MTU
from threading import Event

#region Exceptions
class Not4Me(Exception):
    pass

class ConnectionClose(Exception):

    def __init__(self, reason:bytes):
        self.reason = reason

class AlreadyInCache(Exception):
    pass

class OpenAck(Exception):
    pass

class TrAck(Exception):
    pass

class NotExpectedTrNumber(Exception):
    pass

class MessageDropped(Exception):
    pass
#endregion

class DeviceConnection:

    def __init__(self, link_id: int):
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
        self.open_ack_evt = Event()

        scheduler.spawn_task(f'_clear_cache_t{link_id}', self._clear_cache_t)

#region Tasks
    def _clear_cache_t(self):
        while self.is_alive:
            clear_timer = Timer(self.clear_cache_timeout)
            scheduler.wait_timer(f'_clear_cache_task{self.link_id}', clear_timer)
            yield
            self.cache = []
    
    def get_last_transaction_t(self):
        while len(self.recv_transactions) == 0:
            yield
        last_recv_transaction = self.recv_transactions[0]
        self.recv_transactions = self.recv_transactions[1:]
        yield last_recv_transaction
#endregion

#region Private
    def _is4me(self, content: bytes):
        return content[0:4] == int(self.link_id).to_bytes(4, 'big')

    def _already_in_cache(self, content: bytes):
        return content in self.cache

    def _is_tr_ack(self, content: bytes):
        return content[4] == self.prov_tr_number and content[5] == 0x01

    def _has_correct_tr_number(self, content: bytes):
        return content[4] == self.device_tr_number

    def _is_close_conn(self, content: bytes):
        return content[5] == 0x0b

    def _is_open_ack(self, content: bytes):
        return content[4] == self.prov_tr_number and content[5] == 0x07

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
#endregion

#region Public
    def kill(self):
        self.is_alive = False

    # TODO: Review add_recv_message
    def add_recv_message(self, content: bytes):
        if not self._is4me(content):
            raise Not4Me()
        if self._already_in_cache(content):
            raise AlreadyInCache()
        if self._is_close_conn(content):
            raise ConnectionClose(content[5:6])
        if self._is_open_ack(content):
            raise OpenAck()
        if self._is_tr_ack(content):
            self.prov_tr_number += 1
            raise TrAck()
        if not self._has_correct_tr_number(content):
            raise NotExpectedTrNumber()

        content = content[5:]

        if self.tr_status == 'start':
            first_byte = content[0]
            if first_byte & 0x03 != 0:
                raise MessageDropped()

            self.segn = (first_byte & 0xfc) >> 2
            self.tr_len = int.from_bytes(content[1:3], 'big')
            self.fcs = content[3]
            self.messages[0] = content[4:]
        elif self.tr_status == 'continuation':
            first_byte = content[0]
            if first_byte & 0x03 != 2:
                self.tr_status = 'start'
                raise MessageDropped()

            seg_index = (first_byte & 0xfc) >> 2
            self.messages[seg_index] = content[1:]

        if len(self.messages) - 1 < self.segn:
            self.tr_status = 'continuation'
        else:
            self._validate_message()

        self.cache.append(content)

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

    def get_header(self):
        return self.link_id.to_bytes(4, 'big') + self.prov_tr_number.to_bytes(1, 'big')
#endregion
