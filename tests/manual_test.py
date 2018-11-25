from core.dongle import DongleDriver
from core.gprov import Gprov
from serial import Serial

ser = Serial()
ser.port = '/dev/ttyACM1'
ser.baudrate = 115200

driver = DongleDriver(ser)
driver.dongle_communication_task()

gprov_layer = Gprov(driver)
gprov_layer.open_link(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xdd\xdd')
gprov_layer.send_transaction(b'\x00\x05')
gprov_layer.get_transaction()
