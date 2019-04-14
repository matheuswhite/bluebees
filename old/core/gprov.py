from core.utils import threaded, timeit
from core.link import Link
from core.transaction import Transaction
from threading import Event
from time import sleep
from core.log import Log, LogLevel
from core.scheduling import scheduler, Task, TaskError
from core.utils import crc8
from core.dongle import ADV_MTU
from core.device_connection import DeviceConnection, ConnectionClose, OpenAck, TrAck
from enum import Enum
from random import randint
from core.dongle import DongleDriver

log = Log('Gprov', LogLevel.Succ)
log.disable()

LINK_TIMEOUT = 0x01
CONNECTION_ALREADY_OPEN = 0x02
TR_ACK_TIMEOUT = 0x03
CONNECTION_CLOSE = 0x04

class GenericProvisioner:

    def __init__(self, dongle_driver: DongleDriver):
        self.driver = dongle_driver
        self.connections = {}
        self.is_alive = True

        self._recv_task = scheduler.spawn_task(self._recv_t)

#region Tasks
    def _recv_t(self, self_task: Task):
        while self.is_alive:
            recv_message = self.driver.recv('prov')

            if not recv_message:
                yield
                continue

            # log.dbg(f'Message received: {recv_message}')

            for k in list(self.connections.keys()):
                try:
                    conn = self.connections[k]
                    conn.add_recv_message(recv_message)

                except ConnectionClose as ex:
                    conn.is_alive = False
                    # del self.connections[k]
                finally:
                    yield

    """
    Usage
    
    open_task = scheduler.spawn_task(open_connection_t, dev_uuid=b'\x00', connection_id=0xAABBCCDD)
    self_task.wait_finish(open_task)
    yield

    if not open_task.has_error():
        print('Connection with {0xAABBCCDD} established successful')

    Errors
        -> LINK_TIMEOUT
        -> CONNECTION_ALREADY_OPEN
    """
    def open_connection_t(self, self_task: Task, dev_uuid: bytes, connection_id: int):
        # check if connection already is open
        if connection_id not in list(self.connections.keys()):
            # save device connection
            dev_conn = DeviceConnection(connection_id, self.driver)
            self.connections[connection_id] = dev_conn

            # create message and send it
            log.dbg('Send opening message')
            message = dev_conn.get_header() + b'\x03' + dev_uuid
            self.driver.send(2, 20, message)

            # wait open ack
            log.dbg('Wait open ack')
            self_task.wait_event(event=dev_conn.open_ack_evt, timeout=30)
            yield

            if not dev_conn.open_ack_evt.isSet() or self_task.timer.elapsed_time > self_task.timer.timeout:
                log.err(f'Connection open fail. Link_id {dev_conn.link_id}')
                # dev_conn.is_alive = False
                # del self.connections[connection_id]
                raise TaskError(LINK_TIMEOUT, f'Link {connection_id} open timeout')

            dev_conn.open_ack_evt.clear()
            log.succ('Open ack received')
        else:
            raise TaskError(CONNECTION_ALREADY_OPEN, f'Link {connection_id} is already open')

    """
    Usage
    
    get_tr_task = scheduler.spawn_task(get_transaction_t, connection_id=0xAABBCCDD)
    self_task.wait_finish(get_tr_task)
    yield

    tr_recv = get_tr_task.get_first_result()

    Errors
        -> CONNECTION_CLOSE
    """
    def get_transaction_t(self, self_task: Task, connection_id: int):
        self._handle_link_close_message(connection_id)
        conn = self.connections[connection_id]
        
        log.dbg('Waiting transaction')
        tr_recv = None
        while tr_recv is None:
            self._handle_link_close_message(connection_id)
            tr_recv = conn.get_last_transaction()
            yield

        log.dbg(f'Transaction Received: {tr_recv}')

        # create ack message and send it
        # message = conn.get_header() + b'\x01'
        # self.driver.send(2, 20, message)

        yield tr_recv

    """
    Usage
    
    snd_tr_task = scheduler.spawn_task(send_transaction_t, connection_id=0xAABBCCDD, content=b'Message')
    self_task.wait_finish(snd_tr_task)
    yield

    Errors
        -> TR_ACK_TIMEOUT
        -> CONNECTION_CLOSE
    """
    def send_transaction_t(self, self_task: Task, connection_id: int, content: bytes):
        self._handle_link_close_message(connection_id)
        messages = self.connections[connection_id].mount_snd_transaction(content)

        for msg in messages:
            log.dbg(f'Segment: {msg}')
            self.driver.send(2, 20, msg)
            delay = randint(20, 50) / 1000.0
            sleep(delay)

        self._handle_link_close_message(connection_id)
        dev_conn = self.connections[connection_id]

        # waiting tr ack
        self._handle_link_close_message(connection_id)
        self_task.wait_event(dev_conn.tr_ack_event, timeout=30)
        yield

        self._handle_link_close_message(connection_id)
        if not dev_conn.tr_ack_event.isSet() or self_task.timer.elapsed_time > self_task.timer.timeout:
            log.err(f'Cannot receive tr ack. Link_id {dev_conn.link_id}, Content {content}')
            raise TaskError(TR_ACK_TIMEOUT, f'Wait Transaction Ack timeout. Transaction: {content}')

        self._handle_link_close_message(connection_id)
        dev_conn.tr_ack_event.clear()
        log.succ('Transaction ack received')
#endregion

#region Private
    def _is_ack_message(self, message: bytes):
        return message[0:1] == b'0x07'

    def _handle_link_close_message(self, connection_id: int):
        if not self.connections[connection_id].is_alive:
            raise TaskError(CONNECTION_CLOSE, f'Connection {self.connections[connection_id].link_id} closed by device')
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
#endregion
