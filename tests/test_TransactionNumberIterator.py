from unittest import TestCase
from core.provisioning_link import TransactionNumberIterator


class TestTransactionNumberIterator(TestCase):

    def test_provisioner_mode(self):
        tr_number = TransactionNumberIterator(is_provisioner=True)

        result = []
        for x in range(0, 0x81):
            result.append(next(tr_number))

        expected = list(range(0x00, 0x80))
        expected.append(0x00)

        self.assertEqual(expected, result)

    def test_device_mode(self):
        tr_number = TransactionNumberIterator(is_provisioner=False)

        result = []
        for x in range(0, 0x81):
            result.append(next(tr_number))

        expected = list(range(0x80, 0x100))
        expected.append(0x80)

        self.assertEqual(expected, result)
