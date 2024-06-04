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


class Sentinel2(ee.ImageCollection):
    @classmethod
    def surface_reflectance(cls):
        return cls("COPERNICUS/S2_SR_HARMONIZED")

    @classmethod
    def top_of_atmosphere(cls):
        return cls("COPERNICUS/S2_HARMONIZED")

    def __init__(self, args: Any):
        super().__init__(args)

    def filterCloud(self, percent: float):
        return self.filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", percent))

    def applyCloudMask(self):
        return self.map(self.cloud_mask)

    @staticmethod
    def cloud_mask(image: ee.Image):
        qa = image.select("QA60")
        # Bits 10 and 11 are clouds and cirrus, respectively.
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        # Both flags should be set to zero, indicating clear conditions.
        mask = (
            qa.bitwiseAnd(cloud_bit_mask)
            .eq(0)
            .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        )

        return image.updateMask(mask)


class AlosPalsar(ee.ImageCollection):
    def __init__(self):
        super().__init__('JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH')