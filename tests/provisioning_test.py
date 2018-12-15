from core.provisioning import ProvisioningLayer
from core.gprov import Gprov
from core.dongle import DongleDriver
from serial import Serial


if __name__ == '__main__':
    ser = Serial()
    ser.baudrate = 115200
    ser.port = '/dev/ttyACM1'

    driver = DongleDriver(ser)
    driver.dongle_communication_task()

    gprov = Gprov(driver)

    prov = ProvisioningLayer(gprov, driver)

    device_uuid = b'\xdd\xdd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    net_key = b'\xe6\x78\xf5\xe9\x96\x75\x1a\x9f\x69\xff\x76\xe8\xf6\xad\x3d\x04'
    key_index = 0
    iv_index = b'\x00\x00\x00\x00'
    unicast_address = b'\x00\x0a'

    prov.provisioning_device(device_uuid, net_key, key_index, iv_index, unicast_address)

    while True:
        pass
