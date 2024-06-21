from __future__ import annotations
from typing import Any
import ee
import geopandas as gpd


class RemoteSensingDataset(ee.ImageCollection):
    """Base class for a class that relates to RSD"""

    def __init__(self, args: Any):
        super().__init__(args)

    def toFeatureCollection(self) -> ee.FeatureCollection:
        """Converts the Current Collection to a FeatureCollection copies all properties"""
        ic_list = self.toList(self.size())
        f_list = ic_list.map(self.img2features)
        return ee.FeatureCollection(f_list)

    def toGeoPandasDataFrame(self) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame.from_features(
            self.toFeatureCollection().getInfo()["features"]
        )

    @staticmethod
    def img2features(image) -> ee.Feature:
        image = ee.Image(image)
        geom = image.geometry()
        props = image.propertyNames()
        return ee.Feature(geom, image.toDictionary(props))


class Sentinel1(RemoteSensingDataset):
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
        super().__init__("JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH")


class NASADEM(ee.Image):
    """for more info go to https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001?hl=en"""

    def __init__(self):
        super().__init__("NASA/NASADEM_HGT/001")


class LansatSurfaceReflectance(RemoteSensingDataset):
    def __init__(self, args: Any):
        super().__init__(args)
    
    def filterClouds(self, percent: float):
        return self.filter(ee.Filter.lte("CLOUD_COVER", percent))

    def applyCloudMask(self):
        return self.map(self.cloud_mask)

    def applyScalingFactor(self):
        return self.map(self.scaling_factors)

    def rename(self):
        """renames bands to match land sat 8"""
        old_names = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"]
        new_name = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
        return self.select(old_names, new_name)

    @staticmethod
    def cloud_mask(image):
        """mask clouds and applies scaling factor"""
        qaMask = image.select("QA_PIXEL").bitwiseAnd(int("11111", 2)).eq(0)
        saturationMask = image.select("QA_RADSAT").eq(0)

        return (
            image.set({"cloud_mask": 1}).updateMask(qaMask).updateMask(saturationMask)
        )

    @staticmethod
    def scaling_factors(image: ee.Image):
        optical_bands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
        thermal_bands = image.select("ST_B6").multiply(0.00341802).add(149.0)
        return (
            image.set({"scaling_factor": 1})
            .addBands(optical_bands, None, True)
            .addBands(thermal_bands, None, True)
        )


class Landsat5SR(LansatSurfaceReflectance):
    def __init__(self):
        super().__init__("LANDSAT/LT05/C02/T1_L2")


class Landsat8SR(LansatSurfaceReflectance):
    def __init__(self):
        super().__init__("LANDSAT/LC08/C02/T1_L2")

    @staticmethod
    def scaling_factors(image: ee.Image):
        optical_bands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
        thermal_bands = image.select("ST_B.*").multiply(0.00341802).add(149.0)
        return (
            image.set({"scaling_factor": 1})
            .addBands(optical_bands, None, True)
            .addBands(thermal_bands, None, True)
        )

