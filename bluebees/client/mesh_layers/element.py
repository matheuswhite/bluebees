from bluebees.client.mesh_layers.transport_layer import TransportLayer, AckTimeout
from bluebees.client.mesh_layers.mesh_context import SoftContext
from bluebees.client.mesh_layers.address import address_type, UNICAST_ADDRESS, \
                                       UNASSIGNED_ADDRESS
from bluebees.client.mesh_layers.access_layer import check_opcode, check_parameters, \
                                            OpcodeLengthError, \
                                            OpcodeBadFormat, OpcodeReserved, \
                                            ParametersLengthError, opcode_len
from bluebees.common.logging import log_sys, INFO, DEBUG
from bluebees.common.client import Client
import asyncio
import traceback


class SrcAddressError(Exception):
    pass


class DstAddressError(Exception):
    pass


class Element(Client):

    def __init__(self):
        super().__init__(sub_topic_list=[b'message'],
                         pub_topic_list=[b'message_s'])
        self.log = log_sys.get_logger('element')
        self.log.set_level(INFO)

        self.tr_layer = TransportLayer(send_queue=self.messages_to_send,
                                       recv_queue=self.messages_received)

        self.all_tasks += [self.tr_layer.net_layer.recv_pdu()]

    async def send_message(self, opcode: bytes, parameters: bytes,
                           ctx: SoftContext):
        try:
            success = False

            if address_type(ctx.src_addr) != UNICAST_ADDRESS:
                raise SrcAddressError
            if address_type(ctx.dst_addr) == UNASSIGNED_ADDRESS:
                raise DstAddressError

            check_opcode(opcode)
            check_parameters(opcode, parameters)

            pdu = opcode + parameters

            success = await self.tr_layer.send_pdu(pdu, ctx)
        except OpcodeLengthError:
            self.log.error('Opcode length wrong')
        except OpcodeReserved:
            self.log.error('Opcode reserved for future use')
        except OpcodeBadFormat:
            self.log.error('Opcode bad format')
        except ParametersLengthError:
            self.log.error('Parameter length wrong')
        except SrcAddressError:
            self.log.error(f'The source address must be a unicast address')
        except DstAddressError:
            self.log.error(f'The destination address cannot be 0x0000')
        except AckTimeout:
            self.log.warning('Ack timeout')
        # except Exception:
        #     self.log.error(traceback.format_exc())
        finally:
            return success

    async def _recv_message_atomic(self, opcode: bytes,
                                   segment_timeout: int,
                                   ctx: SoftContext) -> bytes:
        while True:
            self.log.debug('Waiting message atomic...')
            content, _ = await self.tr_layer.recv_pdu(segment_timeout, ctx)
            if not content:
                self.log.debug('No content')
                continue
            self.log.debug('Get opcode len')
            op_len = opcode_len(content[0:1])
            self.log.debug(f'Opcode len: {op_len}')
            self.log.debug(f'Opcode: {content[0:op_len].hex()}')
            if content[0:op_len] == opcode:
                return content[op_len:]

    async def recv_message(self, opcode: bytes, ctx: SoftContext,
                           segment_timeout=10, timeout=30) -> bytes:
        content = None

        self.log.debug('Start recv...')

        try:
            self.log.debug('Checking opcode...')
            check_opcode(opcode)
            self.log.debug('Opcode is ok')
            content = await asyncio.wait_for(self._recv_message_atomic(
                opcode, segment_timeout, ctx), timeout=timeout)
            self.log.debug('End receive')
        except OpcodeLengthError:
            self.log.error('Opcode length wrong')
        except OpcodeReserved:
            self.log.error('Opcode reserved for future use')
        except OpcodeBadFormat:
            self.log.error('Opcode bad format')
        except asyncio.TimeoutError:
            self.log.debug(f'The maximum time to receive a message with '
                           f'opcode equals to "{opcode.hex()}" was reached')

        if content:
            self.log.debug(f'Content: {content.hex()}')

        return content
