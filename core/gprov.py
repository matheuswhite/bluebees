from core.utils import threaded, timeit
from core.link import Link
from core.transaction import Transaction
from threading import Event
from time import sleep
from core.log import Log
from core.scheduling import scheduler, Timer
from core.utils import crc8
from core.dongle import MAX_MTU
from core.device_connection import DeviceConnection, Not4Me, ConnectionClose, AlreadyInCache, OpenAck, \
                                    TrAck, NotExpectedTrNumber, MessageDropped
from enum import Enum
from random import randint

log = Log('Gprov')

class RetStatus(Enum):
    LinkOpenSuccessful=0
    LinkOpenTimeout=1
    LinkOpenFail=2

class GenericProvisioner:

    def __init__(self, dongle_driver):
        self.driver = dongle_driver
        self.connections = {}
        self.is_alive = True

        scheduler.spawn_task('_recv_task', self._recv_t())

#region Tasks
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
                    log.dbg(f'Expected {conn.link_id} link_id, but received {recv_message[0:4]} link_id')
                except ConnectionClose as ex:
                    log.err(f'Connection {conn.link_id} closed by device. Reason: {ex.reason}')
                    conn.is_alive = False
                    del self.connections[k]
                except AlreadyInCache:
                    log.dbg(f'Message already in cache. Message: {recv_message}')
                except OpenAck:
                    if conn.is_alive:
                        conn.open_ack_evt.set()
                        log.succ(f'Open ack successfull. Link_id: {conn.link_id}')
                except TrAck:
                    log.succ(f'Tr ack received. Tr number: {recv_message[4]}')
                except NotExpectedTrNumber:
                    log.dbg(f'Expected {conn.prov_tr_number} tr_number, but received {recv_message[4]} tr number')
                except MessageDropped:
                    log.wrn(f'Message was dropped because opcode is wrong. Message {recv_message}')
                finally:
                    yield

    def open_connection_t(self, dev_uuid: bytes, connection_id: int):
        # check if connection already is open
        if connection_id not in list(self.connections.keys()):
            # save device connection
            dev_conn = DeviceConnection(connection_id)
            self.connections[connection_id] = dev_conn

            # create message and send it
            message = dev_conn.get_header() + b'\x03' + dev_uuid
            self.driver.send(2, 20, message)

            # wait open ack
            open_ack_timer = Timer(timeout=30)
            scheduler.wait_event(f'open_connection{connection_id}', dev_conn.open_ack_evt, open_ack_timer)
            yield

            if dev_conn.open_ack_evt.isSet() and open_ack_timer.te < open_ack_timer.timeout:
                yield RetStatus.LinkOpenSuccessful
            else:
                log.err(f'Connection open fail. Link_id {conn.link_id}')
                dev_conn.is_alive = False
                del self.connections[connection_id]
                yield RetStatus.LinkOpenTimeout
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
        scheduler.wait_finish(invoker_name, spawned_task_name)

        return ret_queue

    def send_transaction(self, connection_id: int, content: bytes):
        messages = self.connections[connection_id].mount_snd_transaction(content)

        for msg in messages:
            self.driver.send(0, 20, msg)
            delay = randint(20, 50) / 1000.0
            sleep(delay)
#endregion
