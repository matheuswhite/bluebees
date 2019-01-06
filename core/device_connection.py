from core.scheduling import scheduler, Task
from core.utils import crc8
from core.dongle import ADV_MTU
from threading import Event
from core.log import Log

log = Log('DeviceConnection')

#region Exceptions
class ConnectionClose(Exception):

    def __init__(self, reason:bytes):
        self.reason = reason

class OpenAck(Exception):
    pass

class TrAck(Exception):
    pass
#endregion

START_MTU = ADV_MTU - 4
CONT_MTU = ADV_MTU - 1

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
        self.clear_cache_timeout = 60
        self.is_alive = True
        self.open_ack_evt = Event()
        self.tr_ack_event = Event()

        self.clear_cache_task = scheduler.spawn_task(self._clear_cache_t)

    #region Tasks
    def _clear_cache_t(self, self_task: Task):
        while self.is_alive:
            self.clear_cache_task.wait_timer(timeout=self.clear_cache_timeout)
            yield
            log.wrn(f'Cache of connection {self.link_id} cleared')
            self.cache = []
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

        # check transaction integrity
        calc_fcs = crc8(tr_content)
        if self.tr_len == len(tr_content) and self.fcs == calc_fcs:
            self.device_tr_number = ((self.device_tr_number + 1) % 0x80) + 0x80
            self.recv_transactions.append(tr_content)

        self.tr_status = 'start'
    #endregion

    #region Public
    def kill(self):
        self.is_alive = False

    def get_last_transaction(self):
        if len(self.recv_transactions) > 0:
            last_recv_transaction = self.recv_transactions[0]
            self.recv_transactions = self.recv_transactions[1:]
            return last_recv_transaction

    def add_recv_message(self, content: bytes):
        if not self._is4me(content):
            return
        if self._already_in_cache(content):
            return
        else:
            self.cache.append(content)
        if self._is_close_conn(content):
            raise ConnectionClose(content[5:6])
        if self._is_open_ack(content):
            self.open_ack_evt.set()
            return
        if self._is_tr_ack(content):
            self.prov_tr_number += 1
            self.tr_ack_event.set()
            return
        if not self._has_correct_tr_number(content):
            log.wrn('tr number wrong')
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

    def _get_total_seg_number(self, content: bytes):
        total_seg_number = 0
        content_copy = content
        content_copy = content_copy[START_MTU:]
        while len(content_copy) > 0:
            content_copy = content_copy[CONT_MTU:]
            total_seg_number += 1
        return total_seg_number

    # TODO: Review MTU size
    def mount_snd_transaction(self, content: bytes):
        messages = []

        if len(content) == 0:
            return messages

        header = int(self.link_id).to_bytes(4, 'big') + int(self.prov_tr_number).to_bytes(1, 'big')

        # start message
        total_seg_number = self._get_total_seg_number(content)
        segn = (total_seg_number << 2).to_bytes(1, 'big')
        total_length = len(content).to_bytes(2, 'big')
        fcs = crc8(content).to_bytes(1, 'big')
        has_continuation = int.from_bytes(total_length, 'big') > START_MTU
        if has_continuation:
            data = content[0:START_MTU]
            content = content[START_MTU:]
        else:
            data = content
        messages.append(header + segn + total_length + fcs + data)

        # continuation messages
        if has_continuation:
            for i in range(1, total_seg_number):
                seg_index = ((i << 2) | 0x02).to_bytes(1, 'big')
                log.dbg(f'seg_index: {i}')
                data = content[0:CONT_MTU]
                content = content[CONT_MTU:]
                messages.append(header + seg_index + data)
            seg_index = ((total_seg_number << 2) | 0x02).to_bytes(1, 'big')
            messages.append(header + seg_index + content)

        return messages

    def get_header(self):
        return self.link_id.to_bytes(4, 'big') + self.prov_tr_number.to_bytes(1, 'big')
    #endregion
