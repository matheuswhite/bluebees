from unittest import TestCase
from data_structs.buffer import Buffer


class TestBuffer(TestCase):

    def test_push_u8(self):
        buffer = Buffer()
        buffer.push_u8(16)
        buffer.push_u8(0x20)
        buffer.push_u8(b'\x23')

        self.assertEqual(b'\x10\x20\x23', buffer.buffer)

    def test_push_be16(self):
        buffer = Buffer()
        buffer.push_be16(300)
        buffer.push_be16(0x2045)
        buffer.push_be16(b'\x23\x12')

        self.assertEqual(b'\x01\x2c\x20\x45\x23\x12', buffer.buffer)

    def test_push_le16(self):
        buffer = Buffer()
        buffer.push_le16(300)
        buffer.push_le16(0x2045)
        buffer.push_le16(b'\x23\x12')

        self.assertEqual(b'\x2c\x01\x45\x20\x12\x23', buffer.buffer)

    def test_push_be32(self):
        buffer = Buffer()
        buffer.push_be32(70000)
        buffer.push_be32(0x20457908)
        buffer.push_be32(b'\x23\x12\xa6\xf1')

        self.assertEqual(b'\x00\x01\x11\x70\x20\x45\x79\x08\x23\x12\xa6\xf1', buffer.buffer)

    def test_push_le32(self):
        buffer = Buffer()
        buffer.push_le32(70000)
        buffer.push_le32(0x20457908)
        buffer.push_le32(b'\x23\x12\xa6\xf1')

        self.assertEqual(b'\x70\x11\x01\x00\x08\x79\x45\x20\xf1\xa6\x12\x23', buffer.buffer)

    def test_push_be(self):
        buffer = Buffer()
        buffer.push_be(b'\x23\x12\xa6\xf1\x64\x19')

        self.assertEqual(b'\x23\x12\xa6\xf1\x64\x19', buffer.buffer)

    def test_push_le(self):
        buffer = Buffer()
        buffer.push_le(b'\x23\x12\xa6\xf1\x64\x19')

        self.assertEqual(b'\x19\x64\xf1\xa6\x12\x23', buffer.buffer)

    def test_pull_u8(self):
        buffer = Buffer()
        buffer.push_u8(16)
        buffer.push_u8(0x20)
        buffer.push_u8(b'\x23')

        byte = buffer.pull_u8()
        self.assertEqual(b'\x10', byte)

        byte = buffer.pull_u8()
        self.assertEqual(b'\x20', byte)

        byte = buffer.pull_u8()
        self.assertEqual(b'\x23', byte)

    def test_pull_be16(self):
        buffer = Buffer()
        buffer.push_be16(300)
        buffer.push_be16(0x2045)
        buffer.push_be16(b'\x23\x12')

        value = buffer.pull_be16()
        self.assertEqual(b'\x01\x2c', value)

        value = buffer.pull_be16()
        self.assertEqual(b'\x20\x45', value)

        value = buffer.pull_be16()
        self.assertEqual(b'\x23\x12', value)

    def test_pull_le16(self):
        buffer = Buffer()
        buffer.push_le16(300)
        buffer.push_le16(0x2045)
        buffer.push_le16(b'\x23\x12')

        value = buffer.pull_le16()
        self.assertEqual(b'\x01\x2c', value)

        value = buffer.pull_le16()
        self.assertEqual(b'\x20\x45', value)

        value = buffer.pull_le16()
        self.assertEqual(b'\x23\x12', value)

    def test_pull_be32(self):
        buffer = Buffer()
        buffer.push_be32(70000)
        buffer.push_be32(0x20457908)
        buffer.push_be32(b'\x23\x12\xa6\xf1')

        value = buffer.pull_be32()
        self.assertEqual(b'\x00\x01\x11\x70', value)

        value = buffer.pull_be32()
        self.assertEqual(b'\x20\x45\x79\x08', value)

        value = buffer.pull_be32()
        self.assertEqual(b'\x23\x12\xa6\xf1', value)

    def test_pull_le32(self):
        buffer = Buffer()
        buffer.push_le32(70000)
        buffer.push_le32(0x20457908)
        buffer.push_le32(b'\x23\x12\xa6\xf1')

        value = buffer.pull_le32()
        self.assertEqual(b'\x00\x01\x11\x70', value)

        value = buffer.pull_le32()
        self.assertEqual(b'\x20\x45\x79\x08', value)

        value = buffer.pull_le32()
        self.assertEqual(b'\x23\x12\xa6\xf1', value)

    def test_pull_be(self):
        buffer = Buffer()
        buffer.push_be(b'\x23\x12\xa6\xf1\x64\x19')

        value = buffer.pull_be(5)
        self.assertEqual(b'\x23\x12\xa6\xf1\x64', value)

        value = buffer.pull_be(1)
        self.assertEqual(b'\x19', value)

    def test_pull_le(self):
        buffer = Buffer()
        buffer.push_le(b'\x23\x12\xa6\xf1\x64\x19')

        value = buffer.pull_le(5)
        self.assertEqual(b'\x12\xa6\xf1\x64\x19', value)

        value = buffer.pull_le(1)
        self.assertEqual(b'\x23', value)

    def test_pull_all_be(self):
        buffer = Buffer()
        buffer.push_be(b'\x23\x12\xa6\xf1\x64\x19')

        value = buffer.pull_all_be()
        self.assertEqual(b'\x23\x12\xa6\xf1\x64\x19', value)

    def test_pull_all_le(self):
        buffer = Buffer()
        buffer.push_le(b'\x23\x12\xa6\xf1\x64\x19')

        value = buffer.pull_all_le()
        self.assertEqual(b'\x23\x12\xa6\xf1\x64\x19', value)