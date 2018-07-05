from unittest import TestCase
from core.shared_id_pool import SharedIDPool


class TestSharedIDPool(TestCase):

    def test_get_new_id(self):
        pool = SharedIDPool(5)
        result = []

        for x in range(0, 5):
            result.append(pool.get_new_id())

        self.assertEqual(pool.dirty_ids, result)

    def test_get_new_id_cycle(self):
        pool = SharedIDPool(5)
        result = []

        for x in range(0, 6):
            result.append(pool.get_new_id())

        self.assertEqual(pool.dirty_ids, result[5:])
