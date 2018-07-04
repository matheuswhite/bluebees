from unittest import TestCase
from core.shared_id_pool import SharedIDPool


class TestSharedIDPool(TestCase):

    def test_get_new_id(self):
        pool = SharedIDPool(5)

        self.fail()
