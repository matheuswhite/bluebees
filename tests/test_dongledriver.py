from unittest import TestCase
from core.dongle import DongleDriver
from tests.serial_mock import SerialMock


class TestDongleDriver(TestCase):

    def test_send(self):
        read_content = [b'@beacon SGVscA== AA324251bf99\r\n']
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        driver.dongle_communication_task()

        driver.send(2, 20, b'Help')

        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(0, len(ser.temp_write), 'Temp write count')
        self.assertEqual(1, len(ser.write_content), 'Write count')
        self.assertEqual(b'@prov 2 20 SGVscA==\r\n', ser.write_content[0])

    def test_send_29_bytes(self):
        read_content = [b'@beacon SGVscA== AA324251bf99\r\n']
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        driver.dongle_communication_task()

        driver.send(2, 20, b'Help0Help1Help2Help3Help4Help')

        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(0, len(ser.temp_write), 'Temp write count')
        self.assertEqual(1, len(ser.write_content), 'Write count')
        self.assertEqual(b'@prov 2 20 SGVscDBIZWxwMUhlbHAySGVscDNIZWxwNEhlbHA=\r\n', ser.write_content[0])

    def test_send_30_bytes(self):
        read_content = [b'@beacon SGVscA== AA324251bf99\r\n']
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        driver.dongle_communication_task()

        with self.assertRaises(Exception) as context:
            driver.send(2, 20, b'Help0Help1Help2Help3Help4Help5')

        self.assertTrue('Message length greater than 24 bytes' in str(context.exception))
        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(0, len(ser.temp_write), 'Temp write count')
        self.assertEqual(0, len(ser.write_content), 'Write count')

    def test_recv_prov(self):
        read_content = [
            b'@prov SGVscA== AA324251bf99\r\n',
            b'@prov SGVscA== AA324251bf99\r\n',
            b'@prov SGVscA== AA324251bf99\r\n',
            b'@prov SGVscDI= BB324251bf99\r\n',
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        driver.dongle_communication_task()

        content = driver.recv('prov')
        content2 = driver.recv('prov')

        self.assertEqual(b'Help', content)
        self.assertEqual(b'Help2', content2)
        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(2, len(driver.cache.adv_cache), 'Adv cache')
        self.assertEqual(0, len(driver.cache.prov_cache), 'Prov cache')

    def test_recv_beacon(self):
        read_content = [
            b'@beacon SGVscA== AA324251bf99\r\n',
            b'@prov SGVscA== AA334251bf99\r\n',
            b'@beacon SGVscA== AA324251bf99\r\n',
            b'@beacon SGVscDI= BB324251bf99\r\n',
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        driver.dongle_communication_task()

        content = driver.recv('beacon')
        content2 = driver.recv('beacon')

        self.assertEqual(b'Help', content)
        self.assertEqual(b'Help2', content2)
        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(3, len(driver.cache.adv_cache), 'Adv cache')
        self.assertEqual(0, len(driver.cache.beacon_cache), 'Beacon cache')

    def test_recv_limited_tries(self):
        read_content = [
            b'@prov SGVscA== AA324251bf99\r\n',
            b'@prov SGVscA== AA324251bf99\r\n',
            b'@prov SGVscA== AA324251bf99\r\n',
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        driver.dongle_communication_task()

        content = driver.recv('prov')

        content2 = driver.recv('prov', tries=3, interval=0.5)

        self.assertIsNone(content2)
        self.assertEqual(b'Help', content)
        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(1, len(driver.cache.adv_cache), 'Adv cache')
        self.assertEqual(0, len(driver.cache.prov_cache), 'Prov cache')

    def test_send_n_recv(self):
        read_content = [
            b'@prov SGVscA== AA324251bf99\r\n',
            b'@prov SGVscA== AA334251bf99\r\n',
            b'@prov SGVscA== AA324251bf99\r\n',
            b'@beacon SGVscDI= BB324251bf99\r\n',
        ]
        ser = SerialMock(read_content)
        driver = DongleDriver(ser)

        driver.dongle_communication_task()

        driver.send(2, 20, b'Help')
        content = driver.recv('beacon')

        self.assertEqual(0, len(ser.temp_write), 'Temp write count')
        self.assertEqual(1, len(ser.write_content), 'Write count')
        self.assertEqual(b'@prov 2 20 SGVscA==\r\n', ser.write_content[0])
        self.assertEqual(b'Help2', content)
        self.assertEqual(0, len(ser.erros), 'Error count')
        self.assertEqual(3, len(driver.cache.adv_cache), 'Adv cache')
        self.assertEqual(0, len(driver.cache.beacon_cache), 'Beacon cache')
