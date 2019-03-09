from view.page import Page, exit_cmd
from view.element import Element
from clint.textui import indent, colored, puts
from core.provisioning import Provisioning
from core.gprov import GenericProvisioner
from core.dongle import DongleDriver
from serial import Serial
from serial.serialutil import SerialException
from model.mesh_manager import mesh_manager
import platform


class ScanDeviceCommand(Element):

    def __init__(self):
        super().__init__()

    def _config_provisioner(self):
        serial = Serial()
        serial.baudrate = 115200
        serial.port = self._get_serial_port()
        dongle_driver = DongleDriver(serial)
        gprov = GenericProvisioner(dongle_driver)
        provisioning = Provisioning(gprov, dongle_driver)
        return provisioning

    def _get_serial_port(self):
        self.dongle_port = 'COM3' if platform.system() == 'Windows' else '/dev/ttyACM0'
        return self.dongle_port

    def run(self, page, options):
        with indent(len(page.quote) + 1, quote=page.quote):
            try:
                provisioning = self._config_provisioner()
            except SerialException:
                permission = '' if platform.system() == 'Windows' else "Use 'sudo chmod 777 {self.dongle_port}' para " \
                                                                       "dar permissão para o dongle"
                puts(colored.red(f"O dongle não está na porta {self.dongle_port} ou está sem permissão." + permission))
                return exit_cmd

            puts(colored.blue('Procurando por dispositivos...'))
            puts(colored.yellow('Pressione Ctrl+C para cancelar'))

            try:
                while True:
                    dev_uuid = provisioning.scan()
                    puts(colored.green(f'Device {dev_uuid.hex()} found'))
                    mesh_manager.new_device(dev_uuid)
            except KeyboardInterrupt:
                provisioning.kill()


scan_device_page = Page()
scan_device_page += ScanDeviceCommand()
