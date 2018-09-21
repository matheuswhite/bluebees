from core.adv import AdvDriver
from serial import Serial
from random import randint
from core.settings import AdvSettings
from core.utils import threaded

adv_write = AdvDriver('/dev/ttyACM0', 115200)

adv_read = AdvDriver('/dev/ttyACM1', 115200)

lost_msgs = 0


@threaded
def read_cb():
    global lost_msgs
    last_addr = None
    while True:
        payload, addr = adv_read.read('prov')
        # print('Payload: {}, Addr: {}'.format(payload, addr))
        if addr != last_addr:
            last_addr = addr
            if payload == '48656c70':
                lost_msgs -= 1


read_cb()

samples = 100

for x in range(samples):
    payload_ = b'Help'
    print('Msg {}...'.format(x+1))
    adv_write.write(payload=payload_, type_='prov', xmit=2, int_ms=200, endianness='big')
    lost_msgs += 1

print('Lost msgs: {}'.format(lost_msgs))
