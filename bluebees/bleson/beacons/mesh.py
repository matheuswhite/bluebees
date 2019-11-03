from bluebees.bleson.core.roles import Advertiser
from bluebees.bleson.core.types import Advertisement
from bluebees.bleson.interfaces.adapter import Adapter
from bluebees.bleson.logger import log


class MeshBeacon(Advertiser):
    def __init__(self, adapter):
        super().__init__(adapter)
        self.advertisement=Advertisement()

    def set_packet(self, beacon_type: bytes, data: bytes):
        self.beacon_type = beacon_type[0:1]
        self.data = data
        self.len = int(len(data) + 1).to_bytes(1, 'big')

        self.advertisement.raw_data=self.mesh_packet()
        print(f"Beacon Adv raw data = {self.advertisement.raw_data}")

    def mesh_packet(self):
        return self.len + self.beacon_type + self.data
