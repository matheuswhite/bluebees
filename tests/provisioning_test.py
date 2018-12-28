import sys
sys.path.append('/home/matheuswhite/Documentos/bluebees/')

from core.provisioning import Provisioning
from core.gprov import GenericProvisioner
from core.dongle import DongleDriver
from serial import Serial
from core.scheduling import scheduler


if __name__ == '__main__':
    ser = Serial()
    ser.baudrate = 115200
    ser.port = '/dev/ttyACM0'

    driver = DongleDriver(ser)

    gprov = GenericProvisioner(driver)

    prov = Provisioning(gprov, driver)

    device_uuid = b'\xdd\xdd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    net_key = b'\xe6\x78\xf5\xe9\x96\x75\x1a\x9f\x69\xff\x76\xe8\xf6\xad\x3d\x04'
    key_index = 0
    iv_index = b'\x00\x00\x00\x00'
    unicast_address = b'\x00\x0a'

    prov_dev_task = scheduler.spawn_task(prov.provisioning_device_t, connection_id=0xaabbccdd, 
                                            device_uuid=device_uuid, net_key=net_key, key_index=key_index, 
                                            iv_index=iv_index, unicast_address=unicast_address)

    scheduler.run()
