from core.utils import threaded, timeit
from core.link import Link
from core.transaction import Transaction
from threading import Event
from time import sleep
from core.log import Log
from core.scheduling import scheduler, TaskTimer
from core.utils import crc8
from core.dongle import MAX_MTU
from core.device_connection import DeviceConnection, Not4Me, ConnectionClose, AlreadyInCache, OpenAck, \
                                    TrAck, NotExpectedTrNumber, MessageDropped

log = Log('Gprov')


class GenericProvisioner:

    def __init__(self, dongle_driver):
        self.driver = dongle_driver
        self.connections = {}
        self.is_alive = True

        scheduler.spawn_task('_recv_task', self._recv_t())

#region Tasks
    def _ack_timer_t(self):
        timer = TaskTimer()
        timer.timeout = 30
        while True:
            scheduler.wait_timer('_ack_timer', timer)
            yield 'timeout'
            break

    def _recv_t(self):
        while self.is_alive:
            recv_message = self.driver.recv('prov')

            if not recv_message:
                yield
                continue

            for k in list(self.connections.keys()):
                try:
                    conn = self.connections[k]
                    conn.add_recv_message(recv_message)

                except Not4Me:
                    pass
                except ConnectionClose as ex:
                    log.err(f'Connection {conn.link_id} closed by device. Reason: {ex.reason}')
                    conn.is_open = False
                    conn.is_alive = False
                    del self.connections[k]
                except AlreadyInCache:
                    pass
                except OpenAck:
                    conn = True
                except TrAck:
                    pass
                except NotExpectedTrNumber:
                    pass
                except MessageDropped:
                    pass

    def open_connection_ts(self, dev_uuid: bytes, connection_id: int):
        dev_conn = DeviceConnection(connection_id)
        self.connections[connection_id] = dev_conn

        message = dev_conn.get_header() + b'\x03' + dev_uuid
        self.driver.send(2, 20, message)

        # spawn a timer
        timer_status = []
        scheduler.spawn_task(f'_ack_timer_t{connection_id}', self._ack_timer_t(), timer_status)

        # wait ack response
        while not self.connections[connection_id].is_open and 'timeout' not in timer_status:
            yield
#endregion

#region Private
    def _is_ack_message(self, message: bytes):
        return message[0:1] == b'0x07'
#endregion

#region Publc
    def kill(self):
        self.is_alive = False

    def close_connection(self, connection_id: int, reason: int):
        message = self.connections[connection_id].get_header() + b'\x0b' + reason.to_bytes(1, 'big')
        self.driver.send(2, 20, message)

        self.connections[connection_id].is_open = False
        self.connections[connection_id].is_alive = False
        del self.connections[connection_id]

    """
    Usage
        # this will wait a new transaction using scheduler
        ret_queue = gprov.get_transaction('phase0_t', 0x1995)
        yield

        ...
    """
    def get_transaction_s(self, invoker_name: str, connection_id: int) -> list:
        conn = self.connections[connection_id]
        ret_queue = []

        spawned_task_name = f'get_last_transaction_t{connection_id}'
        scheduler.spawn_task(spawned_task_name, conn.get_last_transaction_t(), ret_queue)
        scheduler.set_dependency(invoker_name, spawned_task_name)

        return ret_queue

    def send_transaction(self, connection_id: int, content: bytes):
        messages = self.connections[connection_id].mount_snd_transaction(content)

        for msg in messages:
            self.driver.send(0, 20, msg)
#endregion
