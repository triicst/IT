import unittest
import storage_calculator
from storage_calculator.storage import *
import hashlib


class TestStorageCalculator(unittest.TestCase):
    """
    Test a few calculations
    """

    def setUp(self):
        pass


    def test_first_year_simple(self):
        """
        Test cost calculations for first year only.
        """
        cc = CostCalculator(hss_units=2000, ffs_units=7, es_units=8)
        cc.calculate(year_count=1)
        self.assertEqual('36c1e033f6e7e0a77fa304edb77eb46945dad2676f73b9a59d2e529af8723dcb',
            hashlib.sha256(cc.cost_json()).hexdigest())


    def test_multi_year_simple(self):
        """
        Test cost calculations for multiple years, 5 in this case.
        """
        cc = CostCalculator(hss_units=3000, ffs_units=4, es_units=8,
            unit_growth=0.30, rate_decline=0.20)
        cc.calculate(year_count=5)
        self.assertEqual('c9733de36468357cc03cbcb535b9638b69b664d6291e2f4cfafd0a6ca4ac5d24',
            hashlib.sha256(cc.cost_json()).hexdigest())
