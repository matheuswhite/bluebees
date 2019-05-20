from client.mesh_layers.transport_layer import TransportLayer, AckTimeout
from client.mesh_layers.mesh_context import SoftContext
from client.mesh_layers.address import addres_type, UNICAST_ADDRESS, \
                                       UNASSIGNED_ADDRESS
from client.mesh_layers.access_layer import check_opcode, check_parameters, \
                                            OpcodeLengthError, \
                                            OpcodeBadFormat, OpcodeReserved, \
                                            ParametersLengthError, opcode_len
from common.logging import log_sys, INFO
from common.client import Client
from common.utils import FinishAsync
import asyncio


class SrcAddressError(Exception):
    pass


class DstAddressError(Exception):
    pass


# ! Check the byte order in this layer
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
            if addres_type(ctx.src_addr) != UNICAST_ADDRESS:
                raise SrcAddressError
            if addres_type(ctx.dst_addr) == UNASSIGNED_ADDRESS:
                raise DstAddressError

            check_opcode(opcode)
            check_parameters(opcode, parameters)

            pdu = opcode + parameters
            # pdu = pdu[::-1]

            await self.tr_layer.send_pdu(pdu, ctx)
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
        else:
            await asyncio.sleep(1)
            raise FinishAsync

    async def _recv_message_atomic(self, opcode: bytes,
                                   segment_timeout: int) -> bytes:
        while True:
            content, _ = await self.tr_layer.recv_pdu(segment_timeout)
            if not content:
                continue
            op_len = opcode_len(content[0:1])
            if content[0:op_len] == opcode:
                return content[1:]

    async def recv_message(self, opcode: bytes, segment_timeout=10,
                           timeout=30) -> bytes:
        content = None

        try:
            check_opcode(opcode)
            content = \
                await asyncio.wait_for(self._recv_message_atomic(opcode,
                                                                 segment_timeout),
                                       timeout=timeout)

            content = content[::-1]
        except Exception as e:
            self.log.critical(f'Unknown Exception:\n{e}')
        except OpcodeLengthError:
            self.log.error('Opcode length wrong')
        except OpcodeReserved:
            self.log.error('Opcode reserved for future use')
        except OpcodeBadFormat:
            self.log.error('Opcode bad format')
        except asyncio.TimeoutError:
            self.log.warning(f'The maximum time to receive a message with '
                             f'opcode equals to "{opcode}" was reached')

        return content

# a2ebae
# e4d49718000000000000000000000000
# a2ebaee4d49718000000000000000000000000
