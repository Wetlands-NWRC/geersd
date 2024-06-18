import ee

import unittest

from geersd import RemoteSensingDataset


class TestRemoteSensingDataset(unittest.TestCase):
    def setUp(self) -> None:
        ee.Initialize()
        self.dataset_id = "COPERNICUS/S1_GRD"
        self.start_date = "2019-04-01"
        self.end_date = "2019-05-01"
        self.aoi = ee.Geometry.Point([-77.25155810508264, 44.04800529932478])
        return self

    def test_init(self):
        RemoteSensingDataset(self.dataset_id)

    def test_to_feature_collection(self):
        instance = (
            RemoteSensingDataset(self.dataset_id)
            .filterDate(self.start_date, self.end_date)
            .filterBounds(self.aoi)
            .toFeatureCollection()
        )
        print(instance.first().getInfo())
        self.assertIsInstance(instance, ee.FeatureCollection)

    def test_to_geopandas_data_frame(self):
        import geopandas as gpd

        instance = (
            RemoteSensingDataset(self.dataset_id)
            .filterDate(self.start_date, self.end_date)
            .filterBounds(self.aoi)
            .toGeoPandasDataFrame()
        )
        self.assertIsInstance(instance, gpd.GeoDataFrame)
