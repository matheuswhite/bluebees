from core.scheduling import scheduler, Task, TaskError
from core.gprov import GenericProvisioner, CONNECTION_CLOSE
from core.dongle import DongleDriver
from core.log import Log
from ecdsa import NIST256p, SigningKey
from Crypto.Random import get_random_bytes
from client.crypto import CRYPTO
from ecdsa.ellipticcurve import Point
from model.mesh_manager import mesh_manager
from clint.textui import indent, colored, puts


LINK_CLOSE_SUCCESS = 0x00
LINK_CLOSE_FAIL = 0x02

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
log.disable()


class Provisioning:

    def __init__(self, gprov: GenericProvisioner, dongle_driver: DongleDriver):
        self.is_alive = True
        self.gprov = gprov
        self.dongle_driver = dongle_driver
        self.default_attention_duration = 5
        self.devices = [dev.uuid for dev in list(mesh_manager.devices.values())]

    def _gen_keys(self):
        sk = SigningKey.generate(curve=NIST256p)
        vk = sk.get_verifying_key()

        priv_key = sk.privkey.secret_multiplier
        pub_key = vk.pubkey.point

        return pub_key, priv_key

    # ECDHsecret is 32 bytes, using only 'x' part of pub key
    def _calc_ecdh_secret(self, priv_key, pub_key):
        secret = priv_key * pub_key
        return secret.x()

    def _gen_random_provisioner(self):
        return get_random_bytes(16)

    def kill(self):
        self.is_alive = False

    def scan(self):
        read_data = None
        while read_data is None:
            read_data = self.dongle_driver.recv('beacon')
            if read_data is None:
                continue
            if read_data[1:17] in self.devices or len(read_data) != 23:
                read_data = None
        self.devices.append(read_data[1:17])
        return read_data[1:17]

    """
    Returns
        > default attention duration [int] (invite message content)
        > capabilities [bytes]
    """
    def invitation_phase_t(self, self_task: Task, connection_id: int):
        # send prov invite
        invite_msg = PROVISIONING_INVITE
        invite_msg += self.default_attention_duration.to_bytes(1, 'big')
        send_tr_task = scheduler.spawn_task(self.gprov.send_transaction_t, connection_id=connection_id, content=invite_msg)
        self_task.wait_finish(send_tr_task)
        yield self.default_attention_duration

        if send_tr_task.has_error():
            err: TaskError = send_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)
        
        # recv prov capabilities
        get_tr_task = scheduler.spawn_task(self.gprov.get_transaction_t, connection_id=connection_id)
        self_task.wait_finish(get_tr_task)
        yield

        if get_tr_task.has_error():
            err: TaskError = get_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        tr = get_tr_task.get_first_result()
        opcode = tr[0]
        capabilities = tr[1:]
        if opcode != int.from_bytes(PROVISIONING_CAPABILITIES, 'big'):
            self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(PROVISIONING_FAIL, f'Receive message with opcode {opcode}, but expected {PROVISIONING_CAPABILITIES}')
        else:
            yield capabilities
    
    """
    Returns
        > start message content [bytes]
        > public key [Point]
        > private key [int]
        > device public key [Point]
        > ecdh secret [int]
        > auth value [bytes]
    """
    def exchange_keys_phase_t(self, self_task: Task, connection_id: int, public_key_type: bytes, authentication_method: bytes, 
                                authentication_action: bytes, authentication_size: bytes):
        # send prov start (No OOB)
        start_msg = PROVISIONING_START
        start_msg += b'\x00'
        start_msg += public_key_type
        start_msg += authentication_method
        start_msg += authentication_action
        start_msg += authentication_size
        yield start_msg[1:]

        log.dbg('Sending provisioning start')
        send_tr_task = scheduler.spawn_task(self.gprov.send_transaction_t, connection_id=connection_id, content=start_msg)
        self_task.wait_finish(send_tr_task)
        yield

        if send_tr_task.has_error():
            err: TaskError = send_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        log.dbg('Provisioning start message sent successful')

        # gen priv_key and pub_key
        public_key, priv_key = self._gen_keys()
        yield public_key
        yield priv_key

        # send my pub key
        pub_key_msg = PROVISIONING_PUBLIC_KEY
        pub_key_msg += public_key.x().to_bytes(32, 'big')
        pub_key_msg += public_key.y().to_bytes(32, 'big')

        log.dbg('Sending public key message')
        send_tr_task = scheduler.spawn_task(self.gprov.send_transaction_t, connection_id=connection_id, content=pub_key_msg)
        self_task.wait_finish(send_tr_task)
        yield

        if send_tr_task.has_error():
            err: TaskError = send_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        log.dbg('Public key message sent successful')

        # recv device pub key
        log.dbg('Waiting public key message')
        get_tr_task = scheduler.spawn_task(self.gprov.get_transaction_t, connection_id=connection_id)
        self_task.wait_finish(get_tr_task)
        yield
        
        if get_tr_task.has_error():
            err: TaskError = get_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        tr = get_tr_task.get_first_result()
        opcode = tr[0]
        if opcode != int.from_bytes(PROVISIONING_PUBLIC_KEY, 'big'):
            self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(PROVISIONING_FAIL, f'Receive message with opcode {opcode}, but expected {PROVISIONING_PUBLIC_KEY}')
        
        dev_public_key = Point(curve=NIST256p.curve, 
                                x=int.from_bytes(tr[1:33], 'big'), 
                                y=int.from_bytes(tr[33:65], 'big'))
        yield dev_public_key

        log.dbg('Received public key message')

        # calc ecdh_secret = P-256(priv_key, dev_pub_key)
        ecdh_secret = self._calc_ecdh_secret(priv_key, dev_public_key)
        yield ecdh_secret

        auth_value = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        yield auth_value

        log.dbg('Exchange public keys phase complete')

    """
    Returns
        > confirmation salt [bytes]
        > provisioner random [bytes]
        > device confirmation [bytes]
        > device random [bytes]
    """
    def authentication_phase_t(self, self_task: Task, connection_id: int, provisioning_invite: bytes, provisioning_capabilities: bytes,
                                provisioning_start: bytes, public_key_x: bytes, public_key_y: bytes,
                                device_public_key_x: bytes, device_public_key_y: bytes, ecdh_secret: bytes, auth_value: bytes):
        # calc crypto values need
        confirmation_inputs = provisioning_invite + provisioning_capabilities + provisioning_start + public_key_x + \
                                public_key_y + device_public_key_x + device_public_key_y
        confirmation_salt = CRYPTO.s1(confirmation_inputs)
        yield confirmation_salt
        confirmation_key = CRYPTO.k1(ecdh_secret, confirmation_salt, b'prck')
        random_provisioner = self._gen_random_provisioner()
        yield random_provisioner
        confirmation_provisioner = CRYPTO.aes_cmac(confirmation_key, random_provisioner + auth_value)

        # send confirmation provisioner
        confirmation_msg = PROVISIONING_CONFIRMATION
        confirmation_msg += confirmation_provisioner

        log.dbg('Sending confirmation message')
        send_tr_task = scheduler.spawn_task(self.gprov.send_transaction_t, connection_id=connection_id, content=confirmation_msg)
        self_task.wait_finish(send_tr_task)
        yield

        if send_tr_task.has_error():
            err: TaskError = send_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        log.dbg('Confirmation message sent successful')

        # recv confiramtion device
        log.dbg('Receiving confirmation message from device')
        get_tr_task = scheduler.spawn_task(self.gprov.get_transaction_t, connection_id=connection_id)
        self_task.wait_finish(get_tr_task)
        yield

        if get_tr_task.has_error():
            err: TaskError = get_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        tr = get_tr_task.get_first_result()
        opcode = tr[0]
        if opcode != int.from_bytes(PROVISIONING_CONFIRMATION, 'big'):
            self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(PROVISIONING_FAIL, f'Receive message with opcode {opcode}, but expected {PROVISIONING_CONFIRMATION}')
        recv_confirmation_device = tr[1:]
        yield recv_confirmation_device

        log.dbg('Received confirmation message from device')

        # send random provisioner
        random_msg = PROVISIONING_RANDOM
        random_msg += random_provisioner

        log.dbg('Sending random provisioner message')
        send_tr_task = scheduler.spawn_task(self.gprov.send_transaction_t, connection_id=connection_id, content=random_msg)
        self_task.wait_finish(send_tr_task)
        yield

        if send_tr_task.has_error():
            err: TaskError = send_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        log.dbg('Random provisioner message sent successful')

        # recv random device
        log.dbg('Receiving random message from device')
        get_tr_task = scheduler.spawn_task(self.gprov.get_transaction_t, connection_id=connection_id)
        self_task.wait_finish(get_tr_task)
        yield

        if get_tr_task.has_error():
            err: TaskError = get_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        tr = get_tr_task.get_first_result()
        log.wrn(f'lenght: {get_tr_task.get_first_result()}')
        opcode = tr[0]
        if opcode != int.from_bytes(PROVISIONING_RANDOM, 'big'):
            self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(PROVISIONING_FAIL, f'Receive message with opcode {opcode}, but expected {PROVISIONING_RANDOM}')
        random_device = tr[1:]
        yield random_device

        log.dbg('Received random message from device')

        # check info
        calc_confiramtion_device = CRYPTO.aes_cmac(confirmation_key, random_device + auth_value)

        log.dbg(f'calc: {calc_confiramtion_device}, recv: {recv_confirmation_device}')

        if recv_confirmation_device != calc_confiramtion_device:
            self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(PROVISIONING_FAIL, f'Confirmations not match')

        log.dbg('Authentication phase complete')

    """
    Returns
        Nothing
    """
    def send_provisioning_data_phase_t(self, self_task: Task, connection_id: int, network_key: bytes, key_index: bytes, 
                                        flags: bytes, iv_index: bytes, unicast_address: bytes, confirmation_salt: bytes,
                                        random_provisioner: bytes, random_device: bytes, ecdh_secret: bytes):
        # encrypt provisioning data
        provisioning_inputs = confirmation_salt + random_provisioner + random_device
        provisioning_data = network_key + key_index + flags + iv_index + unicast_address
        
        provisioning_salt = CRYPTO.s1(provisioning_inputs)
        session_key = CRYPTO.k1(ecdh_secret, provisioning_salt, b'prsk')
        session_nonce = CRYPTO.k1(ecdh_secret, provisioning_salt, b'prsn')[3:]

        encrypted_provisioning_data, provisioning_data_mic = CRYPTO.aes_ccm_complete(session_key, session_nonce,
                                                                                     provisioning_data, b'')

        # send provisioning data
        provisioning_data_msg = PROVISIONING_DATA
        provisioning_data_msg += encrypted_provisioning_data
        provisioning_data_msg += provisioning_data_mic

        log.log(f'{len(network_key)}/{len(key_index)}/{len(flags)}/{len(iv_index)}/{len(unicast_address)}')

        log.dbg('Sending provisioning data message')
        send_tr_task = scheduler.spawn_task(self.gprov.send_transaction_t, connection_id=connection_id, content=provisioning_data_msg)
        self_task.wait_finish(send_tr_task)
        yield

        if send_tr_task.has_error():
            err: TaskError = send_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        log.dbg('Provisioning data message sent successful')

        # wait prov complete
        log.dbg('Receiving provisioning complete message from device')
        get_tr_task = scheduler.spawn_task(self.gprov.get_transaction_t, connection_id=connection_id)
        self_task.wait_finish(get_tr_task)
        yield

        if get_tr_task.has_error():
            err: TaskError = get_tr_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(err.errno, err.message)

        tr = get_tr_task.get_first_result()
        opcode = tr[0]
        if opcode != int.from_bytes(PROVISIONING_COMPLETE, 'big'):
            self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(PROVISIONING_FAIL, f'Receive message with opcode {opcode}, but expected {PROVISIONING_RANDOM}')

        log.dbg('Received provisioning complete message from device')

        # close link
        self.gprov.close_connection(connection_id, LINK_CLOSE_SUCCESS)

        log.dbg('Send provisioning data phase complete')

    def provisioning_device_t(self, self_task: Task, connection_id: int, device_uuid: bytes, net_key: bytes, key_index: int, iv_index: bytes,
                                unicast_address: bytes):
        # open phase
        puts(colored.blue(f'Tentando se conectar com o dispositivo...'))
        log.dbg('open connection')
        open_task = scheduler.spawn_task(self.gprov.open_connection_t, dev_uuid=device_uuid, connection_id=connection_id)
        self_task.wait_finish(open_task)
        yield

        if open_task.has_error():
            log.err('open error')
            err: TaskError = open_task.errors[0]
            if err.errno != CONNECTION_CLOSE:
                self.gprov.close_connection(connection_id, LINK_CLOSE_FAIL)
            raise TaskError(PROVISIONING_FAIL, f'Cannot open connection {connection_id}')

        puts(colored.green(f'Conexão estabelecida.'))

        # invite phase
        puts(colored.blue(f'Configuração em 0%.'))
        log.dbg('invite phase')
        invite_phase_task = scheduler.spawn_task(self.invitation_phase_t, connection_id=connection_id)
        self_task.wait_finish(invite_phase_task)
        yield

        if invite_phase_task.has_error():
            log.err(f'invite error: {invite_phase_task.errors[0].message}')
            raise TaskError(PROVISIONING_FAIL, f'Invitation phase error')

        log.dbg(f'Capabilities: {invite_phase_task.get_last_result()}')

        log.wrn('Waiting a little bit')
        self_task.wait_timer(5)
        yield

        # exchange keys phase
        puts(colored.blue(f'Configuração em 25%.'))
        log.dbg('exchange keys phase')
        exchange_keys_phase_task = scheduler.spawn_task(self.exchange_keys_phase_t, connection_id=connection_id,
                                                        public_key_type=b'\x00', authentication_method=b'\x00',
                                                        authentication_action=b'\x00', authentication_size=b'\x00')
        self_task.wait_finish(exchange_keys_phase_task)
        yield

        if exchange_keys_phase_task.has_error():
            log.err(f'exchange keys error: {exchange_keys_phase_task.errors[0].message}')
            raise TaskError(PROVISIONING_FAIL, 'Exchange keys phase error')

        log.wrn('Waiting a little bit')
        self_task.wait_timer(5)
        yield

        # authentication phase
        puts(colored.blue(f'Configuração em 50%.'))
        log.dbg('authentication phase')
        authentication_phase_task = scheduler.spawn_task(self.authentication_phase_t, connection_id=connection_id,
                                                        provisioning_invite=invite_phase_task.results[0].to_bytes(1, 'big'),
                                                        provisioning_capabilities=invite_phase_task.results[1],
                                                        provisioning_start=exchange_keys_phase_task.results[0],
                                                        public_key_x=exchange_keys_phase_task.results[1].x().to_bytes(32, 'big'),
                                                        public_key_y=exchange_keys_phase_task.results[1].y().to_bytes(32, 'big'),
                                                        device_public_key_x=exchange_keys_phase_task.results[3].x().to_bytes(32, 'big'),
                                                        device_public_key_y=exchange_keys_phase_task.results[3].y().to_bytes(32, 'big'),
                                                        ecdh_secret=exchange_keys_phase_task.results[4].to_bytes(32, 'big'),
                                                        auth_value=exchange_keys_phase_task.results[5])
        self_task.wait_finish(authentication_phase_task)
        yield

        if authentication_phase_task.has_error():
            log.err(f'authentication error: {authentication_phase_task.errors[0].message}')
            raise TaskError(PROVISIONING_FAIL, 'Authentication phase error')

        log.wrn('Waiting a little bit')
        self_task.wait_timer(5)
        yield

        # send provisioning data phase
        puts(colored.blue(f'Configuração em 75%.'))
        log.dbg('send provisioning data phase')
        flags = b'\x00'

        send_provisioning_data_phase_task = scheduler.spawn_task(self.send_provisioning_data_phase_t,
                                                                    connection_id=connection_id, network_key=net_key,
                                                                    key_index=key_index, flags=flags, iv_index=iv_index,
                                                                    unicast_address=unicast_address,
                                                                    confirmation_salt=authentication_phase_task.results[0],
                                                                    random_provisioner=authentication_phase_task.results[1],
                                                                    random_device=authentication_phase_task.results[3],
                                                                    ecdh_secret=exchange_keys_phase_task.results[4].to_bytes(32, 'big'))
        self_task.wait_finish(send_provisioning_data_phase_task)
        yield

        if send_provisioning_data_phase_task.has_error():
            log.err(f'send provisioning data error: {send_provisioning_data_phase_task.errors[0].message}')
            raise TaskError(PROVISIONING_FAIL, 'Send provisioning data phase error')

        log.succ('send provisioning data finished')

        puts(colored.green(f'Configuração em 100%.'))

        scheduler.kill()
