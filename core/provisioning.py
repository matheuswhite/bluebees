from core.scheduling import scheduler, Task, TaskError
from core.gprov import GenericProvisioner
from core.dongle import DongleDriver
from core.log import Log

PROVISIONING_FAIL = 0x10
PROVISIONING_TIMEOUT = 0x11

PROVISIONING_INVITE = b'\x00'
PROVISIONING_CAPABILITIES = b'\x01'
PROVISIONING_START = b'\x02'
PROVISIONING_PUBLIC_KEY = b'\x03'
PROVISIONING_INPUT_COMPLETE = b'\x04'
PROVISIONING_CONFIRMATION = b'\x05'
PROVISIONING_RANDOM = b'\x06'
PROVISIONING_DATA = b'\x07'
PROVISIONING_COMPLETE = b'\x08'
PROVISIONING_FAILED = b'\x09'

log = Log('Provisioning')

class Provisioning:

    def __init__(self, gprov: GenericProvisioner, dongle_driver: DongleDriver):
        self.is_alive = True
        self.gprov = gprov
        self.dongle_driver = dongle_driver
        self.default_attention_duration = 5

    def invitation_phase_t(self, self_task: Task, connection_id: int):
        # send prov invite
        invite_msg = PROVISIONING_INVITE
        invite_msg += self.default_attention_duration.to_bytes(1, 'big')
        send_tr_task = scheduler.spawn_task(self.gprov.send_transaction_t, connection_id=connection_id, content=invite_msg)
        self_task.wait_finish(send_tr_task)
        yield self.default_attention_duration

        if send_tr_task.has_error():
            err: TaskError = send_tr_task.errors[0]
            raise TaskError(err.errno, err.message)
        
        # recv prov capabilities
        get_tr_task = scheduler.spawn_task(self.gprov.get_transaction_t, connection_id=connection_id)
        self_task.wait_finish(get_tr_task)
        yield

        tr = get_tr_task.get_first_result()
        opcode = tr[0]
        capabilities = tr[1:]
        if opcode != int.from_bytes(PROVISIONING_CAPABILITIES, 'big'):
            raise TaskError(PROVISIONING_FAIL, f'Receive message with opcode {opcode}, but expected {PROVISIONING_CAPABILITIES}')
        else:
            yield capabilities

    def provisioning_device_t(self, self_task: Task, connection_id: int, device_uuid: bytes, net_key: bytes, key_index: int, iv_index: bytes,
                                unicast_address: bytes):
        log.dbg('open connection')
        open_task = scheduler.spawn_task(self.gprov.open_connection_t, dev_uuid=device_uuid, connection_id=connection_id)
        self_task.wait_finish(open_task)
        yield

        if open_task.has_error():
            log.err('open error')
            raise TaskError(PROVISIONING_FAIL, f'Cannot open connection {connection_id}')

        log.dbg('invite phase')
        invite_phase_task = scheduler.spawn_task(self.invitation_phase_t, connection_id=connection_id)
        self_task.wait_finish(invite_phase_task)
        yield

        if invite_phase_task.has_error():
            log.err(f'invite error: {invite_phase_task.errors[0].message}')
            raise TaskError(PROVISIONING_FAIL, f'Invitation phase error')

        log.dbg(f'Capabilities: {invite_phase_task.get_last_result()}')

# from core.utils import timer
# from threading import Event
# from data_structs.buffer import Buffer
# from core.device import Capabilities
# from ecdsa import SigningKey, NIST256p
# from Crypto.Cipher import AES
# from Crypto.Random import get_random_bytes
# from Crypto.Hash import CMAC
# from core.log import Log

# from core.scheduling import scheduler, Task, TaskError
# from random import randint
# from core.gprov import GenericProvisioner
# from core.dongle import DongleDriver

# PROVISIONING_FAIL = 0x10
# PROVISIONING_TIMEOUT = 0x11

# PROVISIONING_INVITE = b'\x00'
# PROVISIONING_CAPABILITIES = b'\x01'
# PROVISIONING_START = b'\x02'
# PROVISIONING_PUBLIC_KEY = b'\x03'
# PROVISIONING_INPUT_COMPLETE = b'\x04'
# PROVISIONING_CONFIRMATION = b'\x05'
# PROVISIONING_RANDOM = b'\x06'
# PROVISIONING_DATA = b'\x07'
# PROVISIONING_COMPLETE = b'\x08'
# PROVISIONING_FAILED = b'\x09'

# CLOSE_SUCCESS = b'\x00'
# CLOSE_TIMEOUT = b'\x01'
# CLOSE_FAIL = b'\x02'

# log = Log('Provisioning')


# class ProvisioningLayer:

#     def __init__(self, gprov: GenericProvisioner, dongle_driver: DongleDriver):
#         self.is_alive = True
#         self.devices = []
#         self.gprov = gprov
#         self.dongle_driver = dongle_driver

#         self.scan_task = scheduler.spawn_task(self._scan_t)

#         self.__device_capabilities = None
#         self.__priv_key = None
#         self.__pub_key = None
#         self.__device_pub_key = None
#         self.__ecdh_secret = None
#         self.__sk = None
#         self.__vk = None
#         self.__provisioning_invite = None
#         self.__provisioning_capabilities = None
#         self.__provisioning_start = None
#         self.__auth_value = None
#         self.__random_provisioner = None
#         self.__random_device = None
#         self.default_attention_duration = 5
#         self.public_key_type = 0x00
#         self.authentication_method = 0x00
#         self.authentication_action = 0x00
#         self.authentication_size = 0x00

# #region Task
#     def _scan_t(self, self_task: Task):
#         while self.is_alive:
#             content = self.dongle_driver.recv('beacon')
#             device = self._process_beacon_content(content)
#             yield
#             if device not in self.devices:
#                 self.devices.append(device)
#             yield
    
#     def invitation_phase_t(self, self_task: Task, connection_id: int):
#         # send prov invite
#         invite_msg = PROVISIONING_INVITE
#         invite_msg += self.default_attention_duration
#         self.gprov.send_transaction(connection_id, invite_msg)
#         yield self.default_attention_duration

#         # recv prov capabilities
#         get_tr_task = scheduler.spawn_task(self.gprov.get_transaction_t, connection_id)
#         self_task.wait_finish(get_tr_task)
#         yield

#         tr = get_tr_task.get_first_result()
#         opcode = tr[0]
#         capabilities = tr[1:]
#         if opcode != PROVISIONING_CAPABILITIES:
#             raise TaskError(PROVISIONING_FAIL, f'Receive message with opcode {opcode}, but expected {PROVISIONING_CAPABILITIES}')
#         else:
#             yield capabilities

#     def provisioning_device_t(self, connection_id: int, device_uuid: bytes, net_key: bytes, key_index: int, iv_index: bytes,
#                                 unicast_address: bytes):
#         provisioning_status = 'ok' # 'ok' | 'timeout' | 'fail'
        
#         # connection open
#         if provisioning_status == 'ok':
#             ret = []
#             scheduler.spawn_task(f'open_connection_t{connection_id}', 
#                                 self.gprov.open_connection_t(device_uuid, connection_id), ret)
#             self._wait_phase(connection_id, f'open_connection_t{connection_id}')
#             yield

#             if ret[0] == RetStatus.LinkOpenTimeout:
#                 provisioning_status = 'timeout'
        
#         # invitation phase
#         if provisioning_status == 'ok':
#             ret = []
#             scheduler.spawn_task(f'_invitation_phase_t{connection_id}', self._invitation_phase_t(), ret)
#             self._wait_phase(connection_id, f'_invitation_phase_t{connection_id}')
#             yield

#             if ret[0]

#         if provisioning_status == 'ok':



#         log.log('Opening Link...')
#         self.__gprov_layer.open_link(device_uuid)
#         log.log('Link Open')

#         try:
#             log.log('Invitation Phase')
#             self.__invitation_prov_phase()
#             log.log('Exchanging Public Keys Phase')
#             self.__exchanging_pub_keys_prov_phase()
#             log.log('Authentication Phase')
#             self.__authentication_prov_phase()
#             log.log('Send Data Phase')
#             self.__send_data_prov_phase(net_key, key_index, iv_index, unicast_address)

#             log.log('Closing Link...')
#             self.__gprov_layer.close_link(CLOSE_SUCCESS)
#             log.log('Link Closed successful')
#         except ProvisioningFail:
#             self.__gprov_layer.close_link(CLOSE_FAIL)
#             log.log('Link Closed with fail')
#         except ProvisioningTimeout:
#             self.__gprov_layer.close_link(CLOSE_TIMEOUT)
#             log.log('Link Closed with timeout')
# #endregion

# #region Private
#     # TODO: change this to get only device uuid
#     def _process_beacon_content(self, content: bytes):
#         if content:
#             return content.split(b' ')[1]

#     def _wait_phase(self, connection_id: int, phase: str):
#         scheduler.wait_finish(f'provisioning_device_t{connection_id}', phase)
# #endregion

# #region Public
#     def kill(self):
#         self.is_alive = False
# #endregion
    


#     def provisioning_device(self, device_uuid: bytes, net_key: bytes, key_index: int, iv_index: bytes,
#                             unicast_address: bytes):
#         log.log('Opening Link...')
#         self.__gprov_layer.open_link(device_uuid)
#         log.log('Link Open')

#         try:
#             log.log('Invitation Phase')
#             self.__invitation_prov_phase()
#             log.log('Exchanging Public Keys Phase')
#             self.__exchanging_pub_keys_prov_phase()
#             log.log('Authentication Phase')
#             self.__authentication_prov_phase()
#             log.log('Send Data Phase')
#             self.__send_data_prov_phase(net_key, key_index, iv_index, unicast_address)

#             log.log('Closing Link...')
#             self.__gprov_layer.close_link(CLOSE_SUCCESS)
#             log.log('Link Closed successful')
#         except ProvisioningFail:
#             self.__gprov_layer.close_link(CLOSE_FAIL)
#             log.log('Link Closed with fail')
#         except ProvisioningTimeout:
#             self.__gprov_layer.close_link(CLOSE_TIMEOUT)
#             log.log('Link Closed with timeout')

    

#     def __invitation_prov_phase(self):
#         # send prov invite
#         send_buff = Buffer()
#         send_buff.push_u8(PROVISIONING_INVITE)
#         send_buff.push_u8(self.default_attention_duration)
#         log.dbg('Sending Invite PDU...')
#         self.__gprov_layer.send_transaction(send_buff.buffer_be())

#         self.__provisioning_invite = self.default_attention_duration

#         # recv prov capabilities
#         recv_buff = Buffer()
#         log.dbg('Receiving Capabilities PDU...')
#         content = self.__gprov_layer.get_transaction()
#         recv_buff.push_be(content)
#         opcode = recv_buff.pull_u8()
#         self.__provisioning_capabilities = recv_buff.buffer_be()
#         log.dbg(b'Opcode: ' + opcode)
#         if opcode != PROVISIONING_CAPABILITIES:
#             raise ProvisioningFail()
#         self.__device_capabilities = Capabilities(recv_buff)

#     def __exchanging_pub_keys_prov_phase(self):
#         # send prov start (No OOB)
#         start_buff = Buffer()
#         start_buff.push_u8(PROVISIONING_START)
#         start_buff.push_u8(0x00)
#         start_buff.push_u8(self.public_key_type)
#         start_buff.push_u8(self.authentication_method)
#         start_buff.push_u8(self.authentication_action)
#         start_buff.push_u8(self.authentication_size)
#         self.__provisioning_start = start_buff.buffer_be()[1:]
#         self.__auth_value = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
#         log.dbg('Sending Start PDU...')
#         self.__gprov_layer.send_transaction(start_buff.buffer_be())

#         # gen priv_key and pub_key
#         self.__gen_keys()

#         # send my pub key
#         pub_key_buff = Buffer()
#         pub_key_buff.push_u8(PROVISIONING_PUBLIC_KEY)
#         pub_key_buff.push_be(self.__pub_key['x'])
#         pub_key_buff.push_be(self.__pub_key['y'])
#         log.dbg('Sending Public Keys PDU...')
#         self.__gprov_layer.send_transaction(pub_key_buff.buffer_be())

#         # recv device pub key
#         recv_buff = Buffer()
#         log.dbg('Receiving Public Key PDU...')
#         content = self.__gprov_layer.get_transaction()
#         log.dbg('Public Key PDU Received')
#         recv_buff.push_be(content)
#         opcode = recv_buff.pull_u8()
#         if opcode != PROVISIONING_PUBLIC_KEY:
#             raise ProvisioningFail()
#         self.__device_pub_key = {
#             'x': recv_buff.pull_be(32),
#             'y': recv_buff.pull_be(32)
#         }

#         # calc ecdh_secret = P-256(priv_key, dev_pub_key)
#         self.__calc_ecdh_secret()

#     def __authentication_prov_phase(self):
#         buff = Buffer()

#         # calc crypto values need
#         confirmation_inputs = self.__provisioning_invite + self.__provisioning_capabilities + \
#                               self.__provisioning_start + self.__pub_key['x'] + self.__pub_key['y'] + \
#                               self.__device_pub_key['x'] + self.__device_pub_key['y']
#         self.__confirmation_salt = self.__s1(confirmation_inputs)
#         confirmation_key = self.__k1(self.__ecdh_secret['x'], self.__confirmation_salt, b'prck')
#         # confirmation_key = self.__k1(self.__ecdh_secret['x'] + self.__ecdh_secret['y'], self.__confirmation_salt,
#         #                              b'prck')

#         self.__gen_random_provisioner()

#         # send confirmation provisioner
#         confirmation_provisioner = self.__aes_cmac(confirmation_key, self.__random_provisioner + self.__auth_value)
#         buff.push_be(confirmation_provisioner)
#         log.dbg('Sending Confirmation PDU...')
#         self.__gprov_layer.send_transaction(buff.buffer_be())

#         # recv confiramtion device
#         log.dbg('Receiving Confirmation PDU...')
#         recv_confirmation_device = self.__recv(opcode_verification=PROVISIONING_CONFIRMATION)

#         # send random provisioner
#         buff.clear()
#         buff.push_be(self.__random_provisioner)
#         log.dbg('Sending Random PDU...')
#         self.__gprov_layer.send_transaction(buff.buffer_be())

#         # recv random device
#         log.dbg('Receiving Random PDU...')
#         self.__random_device = self.__recv(opcode_verification=PROVISIONING_RANDOM)

#         # check info
#         calc_confiramtion_device = self.__aes_cmac(confirmation_key, self.__random_device + self.__auth_value)

#         if recv_confirmation_device != calc_confiramtion_device:
#             raise ProvisioningFail()

#     def __send_data_prov_phase(self, net_key: bytes, key_index: int, iv_index: bytes, unicast_address: bytes):
#         net_key = net_key
#         key_index = int(key_index).to_bytes(2, 'big')
#         flags = b'\x00'
#         iv_index = iv_index
#         unicast_address = unicast_address

#         provisioning_salt = self.__s1(self.__confirmation_salt + self.__random_provisioner + self.__random_device)
#         session_key = self.__k1(self.__ecdh_secret['x'], provisioning_salt, b'prsk')
#         session_nonce = self.__k1(self.__ecdh_secret['x'], provisioning_salt, b'prsn')
#         # session_key = self.__k1(self.__ecdh_secret['x'] + self.__ecdh_secret['y'], self.__provisioning_salt, b'prsk')
#         # session_nonce = self.__k1(self.__ecdh_secret['x'] + self.__ecdh_secret['y'], self.__provisioning_salt,
#                                   # b'prsn')
#         provisioning_data = net_key + key_index + flags + iv_index + unicast_address

#         encrypted_provisioning_data, provisioning_data_mic = self.__aes_ccm(session_key, session_nonce,
#                                                                             provisioning_data)

#         buff = Buffer()
#         buff.push_be(encrypted_provisioning_data)
#         buff.push_be(provisioning_data_mic)
#         log.dbg('Sending Provisioning Data PDU...')
#         self.__gprov_layer.send_transaction(buff.buffer_be())

#         log.dbg('Receiving Complete PDU...')
#         self.__recv(opcode_verification=PROVISIONING_COMPLETE)

#     def __recv(self, opcode_verification=None):
#         buff = Buffer()
#         buff.push_be(self.__gprov_layer.get_transaction())
#         opcode = buff.pull_u8()
#         content = buff.buffer_be()
#         if opcode == PROVISIONING_FAILED:
#             raise ProvisioningFail()
#         if opcode_verification is not None:
#             if opcode != opcode_verification:
#                 raise ProvisioningFail()
#             return content
#         else:
#             return opcode, content

#     def __gen_keys(self):

#         self.__sk = SigningKey.generate(curve=NIST256p)
#         self.__vk = self.__sk.get_verifying_key()

#         self.__priv_key = self.__sk.to_string()
#         self.__pub_key = {
#             'x': self.__vk.to_string()[0:32],
#             'y': self.__vk.to_string()[32:64]
#         }

#     # TODO: ECDHsecret is 32 bytes or 64 bytes
#     def __calc_ecdh_secret(self):
#         secret = self.__sk.privkey.secret_multiplier * self.__vk.pubkey.point

#         self.__ecdh_secret = {
#             'x': secret.x().to_bytes(32, 'big'),
#             'y': secret.y().to_bytes(32, 'big')
#         }

#     def __s1(self, input_: bytes):
#         zero = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
#         return self.__aes_cmac(zero, input_)

#     def __k1(self, shared_secret: bytes, salt: bytes, msg: bytes):
#         okm = self.__aes_cmac(salt, shared_secret)
#         return self.__aes_cmac(okm, msg)

#     def __gen_random_provisioner(self):
#         self.__random_provisioner = get_random_bytes(16)

#     def __aes_cmac(self, key: bytes, msg: bytes):
#         cipher = CMAC.new(key, ciphermod=AES)
#         cipher.update(msg)
#         return cipher.digest()

#     def __aes_ccm(self, key, nonce, data):
#         cipher = AES.new(key, AES.MODE_CCM, nonce)
#         return cipher.encrypt(data), cipher.digest()
