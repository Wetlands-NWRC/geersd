from typing import Any
import ee


class Sentinel1(ee.ImageCollection):
    def __init__(self, args: Any = None):
        self.args = args or "COPERNICUS/S1_GRD"
        super().__init__(self.args)

    def filterVV(self):
        return self.filter(
            ee.Filter.listContains("transmitterReceiverPolarisation", "VV")
        )

    def filterVH(self):
        return self.filter(
            ee.Filter.listContains("transmitterReceiverPolarisation", "VH")
        )

    def filterIWMode(self):
        return self.filter(ee.Filter.eq("instrumentMode", "IW"))

    def filterDesc(self):
        return self.filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))

    def filterAsc(self):
        return self.filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING"))

    def applyEdgeMask(self):
        return self.map(self.edge_mask)

    @staticmethod
    def edge_mask(image: ee.Image) -> ee.Image:
        edge = image.lt(-30.0)
        masked_image = image.mask().And(edge.Not())
        return image.updateMask(masked_image)
